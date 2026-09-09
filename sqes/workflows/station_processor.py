import signal
import os
import time
import numpy as np
import sys
from obspy import UTCDateTime, Trace
from typing import Optional, cast, Dict, Any
from obspy.clients.fdsn import Client as FDSNClient
from obspy.clients.filesystem.sds import Client as SDSClient
from ..services.logging_config import initialize_worker_logger, get_station_logger
from ..core import basic_metrics, ppsd_metrics, models, utils
from ..clients import fdsn, sds, local

# --- Cross-Platform Windows Compatibility Patch ---
if sys.platform == "win32":
    # 1. Provide a dummy integer for SIGALRM so references don't cause an AttributeError
    if not hasattr(signal, "SIGALRM"):
        signal.SIGALRM = 14

    # 2. Provide a dummy alarm function that does nothing
    if not hasattr(signal, "alarm"):
        signal.alarm = lambda time: 0

    # 3. Intercept signal.signal calls to prevent Windows from throwing a ValueError
    _original_signal = signal.signal


    def _win_safe_signal(signum, handler):
        if signum == signal.SIGALRM:
            return None  # Gracefully ignore SIGALRM registration on Windows
        return _original_signal(signum, handler)


    signal.signal = _win_safe_signal
# --------------------------------------------------

# Global Worker Resources
GW_CONTEXT: Dict[str, Any] = {}

#
def init_worker(basic_config, log_level, log_file_path, tgl, time0, time1, client_credentials, output_paths,
                pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False,
                availability=False, head_only=False): # <--- NEW
    """
    Initializer for worker processes.
    Sets up Logging and Context once per process (CSV Mode).
    """
    global GW_CONTEXT

    initialize_worker_logger(log_level, log_file_path)
    logger = get_station_logger("Worker Init")
    logger.debug(f"Worker process started (PID: {os.getpid()})")

    signal.signal(signal.SIGALRM, _handle_timeout)

    GW_CONTEXT.update({
        'tgl': tgl,
        'time0': time0,
        'time1': time1,
        'client_credentials': client_credentials,
        'basic_config': basic_config,
        'output_paths': output_paths,
        'pdf_trigger': pdf_trigger,
        'mseed_trigger': mseed_trigger,
        'qc_thresholds': qc_thresholds,
        'target_prefix': target_prefix,
        'accelerometer': accelerometer,
        'availability': availability, # <--- NEW
        'head_only': head_only        # <--- NEW
    })



def _handle_timeout(signum, frame):
    """Timeout handler for worker processes."""
    print(f"!! Process TIMEOUT after signal {signum}", flush=True)
    raise TimeoutError("Process took too long")


def process_station_data(sta_tuple):
    """
    This is the main worker function that runs in a separate process.
    It processes all components (e.g., E,N,Z or 1,2,Z) for a single station.
    """
    global GW_CONTEXT

    # Unpack Context
    tgl = GW_CONTEXT['tgl']
    time0 = GW_CONTEXT['time0']
    time1 = GW_CONTEXT['time1']
    client_credentials = GW_CONTEXT['client_credentials']
    basic_config = GW_CONTEXT['basic_config']
    output_paths = GW_CONTEXT['output_paths']
    pdf_trigger = GW_CONTEXT['pdf_trigger']
    mseed_trigger = GW_CONTEXT['mseed_trigger']
    qc_thresholds = GW_CONTEXT['qc_thresholds']

    # --- NEW MODE FLAGS ---
    availability_mode = GW_CONTEXT.get('availability', False)
    head_only_mode = GW_CONTEXT.get('head_only', False)
    use_fast_headers = availability_mode and head_only_mode

    try:
        (network, kode, location,
         sistem_sensor, channel_prefixes_str, channel_components_str,
         station_sources) = sta_tuple

        location = location or ''
        raw_prefixes = (channel_prefixes_str or '').split(',')
        channel_components = (channel_components_str or '').split(',')

        target_prefix = GW_CONTEXT.get('target_prefix')
        is_accel = GW_CONTEXT.get('accelerometer', False)

        if target_prefix:
            clean_target = target_prefix.replace(" ", "").upper()
            channel_prefixes = [p.strip() for p in raw_prefixes if p.strip().upper() == clean_target]
            if not channel_prefixes:
                logger = get_station_logger(kode)
                logger.info(
                    f"Skipping {network}.{kode}: Requested prefix '{target_prefix}' not found in station's configured prefixes ({channel_prefixes_str})")
                return
        else:
            channel_prefixes = [p.strip() for p in raw_prefixes if p.strip()]

    except Exception as e:
        print(f"!! FATAL: Error unpacking station tuple {sta_tuple}: {e}", flush=True)
        return

    logger = get_station_logger(kode)
    logger.info(
        f"PROCESS START {network}.{kode} ({sistem_sensor}). Channel: {channel_prefixes}, Components: {channel_components}")

    try:
        waveform_type = basic_config.get('waveform_source', 'fdsn').lower()
        waveform_tag = 'client' if waveform_type == 'fdsn' else 'archive'
        waveform_source_label = f"{waveform_type} ({waveform_tag}) [default]"

        if station_sources and station_sources.waveform:
            waveform_type = station_sources.waveform.type
            waveform_tag = station_sources.waveform.tag
            waveform_source_label = f"{waveform_type} ({waveform_tag})"

        inventory_type = basic_config.get('inventory_source', 'fdsn').lower()
        inventory_tag = 'inventory_client' if inventory_type == 'fdsn' else 'inventory'
        inventory_source_label = f"{inventory_type} ({inventory_tag}) [default]"

        if station_sources and station_sources.inventory:
            inventory_type = station_sources.inventory.type
            inventory_tag = station_sources.inventory.tag
            inventory_source_label = f"{inventory_type} ({inventory_tag})"

        logger.info(f"{network}.{kode} - Waveform: {waveform_source_label}, Inventory: {inventory_source_label}")

        waveform_source = waveform_type
        inventory_source = inventory_type

        from ..services.config_loader import load_client_config, load_archive_config, load_inventory_client_config, \
            load_inventory_path_config

        if waveform_source == 'fdsn':
            waveform_client_config = load_client_config(waveform_tag)
        elif waveform_source == 'sds':
            archive_path = load_archive_config(waveform_tag)

        if inventory_source == 'fdsn':
            if inventory_tag == 'inventory_client':
                try:
                    inventory_client_config = load_inventory_client_config(inventory_tag)
                except:
                    inventory_client_config = waveform_client_config if waveform_source == 'fdsn' else load_client_config(
                        'client')
            else:
                inventory_client_config = load_inventory_client_config(inventory_tag)
        elif inventory_source == 'local':
            inventory_path = load_inventory_path_config(inventory_tag)

        fdsn_client: Optional[FDSNClient] = None
        inventory_fdsn_client: Optional[FDSNClient] = None

        if waveform_source == 'fdsn':
            logger.debug(f"Creating FDSN client for waveforms: {waveform_tag}")
            fdsn_client = FDSNClient(waveform_client_config['url'], user=waveform_client_config['user'],
                                     password=waveform_client_config['password'])

        if inventory_source == 'fdsn':
            logger.debug(f"Creating FDSN client for inventory: {inventory_tag}")
            if waveform_source == 'fdsn' and inventory_tag == waveform_tag:
                inventory_fdsn_client = fdsn_client
            else:
                inventory_fdsn_client = FDSNClient(inventory_client_config['url'], user=inventory_client_config['user'],
                                                   password=inventory_client_config['password'])

        data_client: FDSNClient | SDSClient
        if waveform_source == 'sds':
            if not archive_path:
                logger.error(
                    f"'waveform_source' is 'sds' but archive path is not set for tag '{waveform_tag}'. Worker exiting.")
                return
            data_client = SDSClient(sds_root=archive_path)
        else:
            if not fdsn_client: raise ConnectionError("FDSN client for waveforms was not initialized.")
            data_client = fdsn_client

        if inventory_source == 'local' and not inventory_path:
            logger.error(
                f"'inventory_source' is 'local' but inventory path is not set for tag '{inventory_tag}'. Worker exiting.")
            return

    except Exception as e:
        logger.error(f"Failed to initialize worker resources: {e}")
        return

    outputmseed = output_paths['outputmseed']
    outputsignal = output_paths['outputsignal']
    outputPSD = output_paths['outputPSD']
    outputPDF = output_paths['outputPDF']

    station_metrics_list = []
    availability_list = []  # <--- NEW LIST

    for prefix in channel_prefixes:
        for ch in channel_components:
            cha = f"{prefix}{ch}"
            id_kode = f"{kode}_{cha}_{tgl}"

            logger.warning(f" [DEBUG CP1 - LOOP START] Station: {kode} | Target Channel (cha): '{cha}'")

            def log_default_and_continue(base_metrics=None, cha=cha, reason=""):
                if availability_mode:
                    availability_list.append(
                        {'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha, 'availability': 0.0})
                    logger.warning(f" [DEBUG CP - AVAIL ONLY] {id_kode} Skipped ({reason}). Avail set to 0.0")
                    time.sleep(0.1)
                    return

                logger.warning(f" [DEBUG CP2 - SAVING DETAILS] Station: {kode} | Setting 'cha' column to: '{cha}'")
                if base_metrics:
                    metrics = base_metrics
                else:
                    metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}

                default_full_metrics = {'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha, **metrics,
                                        'pctH': '0', 'pctL': '0', 'dcl': '0', 'dcg': '0', 'long_period': '0',
                                        'microseism': '0', 'short_period': '0'}
                station_metrics_list.append(default_full_metrics)
                logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
                time.sleep(0.5)

            logger.debug(f"{id_kode} Acquiring waveforms (method: {waveform_source})...")
            logger.warning(
                f" [DEBUG CP2.1 - ACQ INPUT] Source: {waveform_source} | Net: '{network}' | Sta: '{kode}' | Loc: '{location}' | Prefix passed: {[prefix]} | Comp passed: '{ch}' | HeadOnly: {use_fast_headers}")

            sig = None
            try:
                if waveform_source == 'sds':
                    sig = sds.get_waveforms(
                        cast(SDSClient, data_client),
                        network, kode, location,
                        [prefix], time0, time1, ch, headonly=use_fast_headers  # <--- PASS FAST FLAG TO SDS
                    )
                else:
                    if not fdsn_client: raise ConnectionError("FDSN client was not initialized (check config).")
                    sig = fdsn.get_waveforms(fdsn_client, network, kode, location, [prefix], time0, time1, ch)

                trace_count = sig.count() if sig else 0
                logger.warning(f" [DEBUG CP2.2 - ACQ SUCCESS] Stream returned {trace_count} trace(s) for {cha}.")

            except TimeoutError:
                logger.error(f"!! {id_kode} download timeout!")
                logger.warning(f" [DEBUG CP2.3 - ACQ TIMEOUT] Timeout while fetching {cha} via {waveform_source}.")
                log_default_and_continue(reason="Download Timeout")
                continue
            except Exception as e:
                logger.error(f"!! {id_kode} data acquisition error: {e}")
                logger.warning(f" [DEBUG CP2.3 - ACQ ERROR] Exception: {type(e).__name__} | Details: {str(e)}")
                log_default_and_continue(reason="Data Acquisition Error")
                continue

            if sig is None or sig.count() == 0:
                logger.info(f"!! {id_kode} No Data found (source: {waveform_source})")
                log_default_and_continue(reason="No Data")
                continue

            logger.debug(f"{id_kode} Waveform acquisition complete")

            # =====================================================================
            # --- NEW: FAST AVAILABILITY MODE SHORT-CIRCUIT ---
            # =====================================================================
            if availability_mode:
                logger.warning(f" [DEBUG CP - AVAIL ONLY] Calculating availability for {cha}")
                try:
                    avail_val = basic_metrics._calculate_percent_availability(sig, time0, time1)
                except Exception as e:
                    logger.error(f"!! {id_kode} availability calculation error: {e}")
                    avail_val = 0.0

                availability_list.append(
                    {'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha, 'availability': avail_val})
                logger.info(f"{id_kode} Availability calculated: {avail_val}%")

                # We skip inventory, plots, basic metrics, and PPSD to save massive time!
                continue

                # --- 2b: Load/Download Inventory ---
            logger.debug(f"{id_kode} Acquiring inventory (method: {inventory_source})...")
            tr = cast(Trace, sig[0])
            inv = None

            if inventory_source == 'local':
                inv = local.get_inventory(cast(str, inventory_path), tr.stats.network, tr.stats.station,
                                          tr.stats.location, tr.stats.channel, time0)
            else:
                if not inventory_fdsn_client: raise ConnectionError(
                    "FDSN client for inventory was not initialized (check config).")
                inv = fdsn.get_inventory(inventory_fdsn_client, tr.stats.network, tr.stats.station, tr.stats.location,
                                         tr.stats.channel, time0)

            if not inv:
                logger.warning(f"!! {id_kode} Got data but NO INVENTORY (source: {inventory_source}). Skipping.")
                log_default_and_continue(reason="No Inventory")
                continue

            # --- 3. Save Waveform & Plot ---
            try:
                signal.alarm(300)
                prefix_part = f"{prefix}_" if prefix else ''
                mseed_naming_code = f"{outputmseed}/{kode}_{prefix_part}{ch}.mseed"
                if mseed_trigger: sig.write(mseed_naming_code)
                sig.plot(outfile=f"{outputsignal}/{kode}_{prefix_part}{ch}_signal.png")
                signal.alarm(0)
            except Exception as e:
                signal.alarm(0)
                logger.error(f"{id_kode} saving exception: {e}")
                log_default_and_continue(cha=cha, reason="Save waveform/plot failed")
                continue

            # --- 4. Process Basic Metrics ---
            try:
                logger.debug(f"{id_kode} Process basic info")
                spike_method = basic_config.get('spike_method', 'fast').lower()
                metrics = basic_metrics.process_basic_metrics(sig, time0, time1, spike_method=spike_method)
                basic_metrics_dict = {
                    'rms': str(round(float(metrics['rms']), 2)),
                    'ratioamp': str(round(float(metrics['ratioamp']), 2)),
                    'psdata': str(round(float(metrics['psdata']), 2)),
                    'ngap': str(int(metrics['ngap'])),
                    'nover': str(int(metrics['nover'])),
                    'num_spikes': str(int(metrics['num_spikes']))
                }
            except Exception as e:
                logger.error(f"{id_kode} basic info exception: {e}")
                log_default_and_continue(cha=cha, reason="Basic metrics failed")
                continue

            # --- 6. Process PPSD Metrics ---
            logger.debug(f"{id_kode} Process PPSD metrics")
            prefix_part = f"{prefix}_" if prefix else ''
            plot_filename = f"{outputPDF}/{kode}_{prefix_part}{ch}_PDF.png"
            npz_path = outputPSD if pdf_trigger else ''

            accel_prefixes_str = basic_config.get('accelerometer_prefixes', 'HN')
            ACCEL_PREFIXES = [p.strip().upper() for p in accel_prefixes_str.split(',') if p.strip()]
            current_is_accel = is_accel or (prefix.upper() in ACCEL_PREFIXES)

            final_metrics = None
            try:
                signal.alarm(1200)
                final_metrics = ppsd_metrics.process_ppsd_metrics(sig, inv, plot_filename=plot_filename,
                                                                  npz_output_path=npz_path,
                                                                  is_accelerometer=current_is_accel)
                signal.alarm(0)
            except TimeoutError:
                signal.alarm(0)
                logger.error(f"{id_kode} PPSD metric processing timed out")
                log_default_and_continue(basic_metrics_dict, cha=cha, reason="PPSD processing timeout")
                continue
            except Exception as e:
                signal.alarm(0)
                logger.error(f"{id_kode} PPSD metric processing failed: {e}")
                log_default_and_continue(basic_metrics_dict, cha=cha, reason="PPSD processing error")
                continue

            if not final_metrics:
                logger.warning(f"{id_kode} PPSD metrics returned None. Skipping with defaults.")
                log_default_and_continue(basic_metrics_dict, cha=cha, reason="PPSD calculation failed")
                continue

            # --- 8. Commit Full Result ---
            all_metrics = {
                'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
                **basic_metrics_dict, **final_metrics
            }
            station_metrics_list.append(all_metrics)

    # =====================================================================
    # --- FINAL RETURN ---
    # =====================================================================

    # If we are in Availability Mode, return early and bypass QC Analysis completely!
    if availability_mode:
        logger.info(f"PROCESS FINISH. Fast availability mode complete.")
        time.sleep(0.1)
        return {
            'kode': kode,
            'tgl': tgl,
            'availability_data': availability_list
        }

    # --- 9. Run QC Analysis ---
    logger.info(f"PROCESS FINISH. Running final analysis in memory...")
    analysis_results = []
    try:
        from ..analysis.qc_analyzer import run_qc_analysis_csv
        analysis_results = run_qc_analysis_csv(kode, tgl, sistem_sensor, station_metrics_list, qc_thresholds)
    except Exception as e:
        logger.error(f"QC Analysis failed for {kode}: {e}")

    time.sleep(0.5)
    return {
        'kode': kode,
        'tgl': tgl,
        'details': station_metrics_list,
        'analysis': analysis_results
    }
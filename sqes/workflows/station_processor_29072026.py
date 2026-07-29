# import signal
# import os
# import time
# import numpy as np
# from obspy import UTCDateTime, Trace
# from typing import Optional, cast, Dict, Any
# from obspy.clients.fdsn import Client as FDSNClient
# from obspy.clients.filesystem.sds import Client as SDSClient
# from ..services.db_pool import DBPool
# from ..services.logging_config import initialize_worker_logger, get_station_logger
# from ..services.repository import QCRepository
# from ..services import source_mapper
# from ..analysis import qc_analyzer
# from ..core import basic_metrics, ppsd_metrics, models, utils
# from ..clients import fdsn, sds, local
#
#
#
#
# import sys
# import signal
#
# # --- Cross-Platform Windows Compatibility Patch ---
# if sys.platform == "win32":
#     # 1. Provide a dummy integer for SIGALRM so references don't cause an AttributeError
#     if not hasattr(signal, "SIGALRM"):
#         signal.SIGALRM = 14
#
#     # 2. Provide a dummy alarm function that does nothing
#     if not hasattr(signal, "alarm"):
#         signal.alarm = lambda time: 0
#
#     # 3. Intercept signal.signal calls to prevent Windows from throwing a ValueError
#     _original_signal = signal.signal
#     def _win_safe_signal(signum, handler):
#         if signum == signal.SIGALRM:
#             return None  # Gracefully ignore SIGALRM registration on Windows
#         return _original_signal(signum, handler)
#     signal.signal = _win_safe_signal
# # --------------------------------------------------
#
#
#
# #
# # # Global Worker Resources
# # GW_DB_POOL: Optional[DBPool] = None
# # GW_CONTEXT: Dict[str, Any] = {}
# #
# # # Remove DBPool and QCRepository imports. Change init_worker to ignore db_credentials.
# # def init_worker(basic_config, log_level, log_file_path, tgl, time0, time1, client_credentials, output_paths, pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False):
# #     # Same as before, but remove DB initialization.
# # # def init_worker(db_credentials, basic_config, log_level, log_file_path,
# # #                 tgl, time0, time1, client_credentials, output_paths,
# # #                 pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False):
# #     """
# #     Initializer for worker processes.
# #     Sets up DBPool, Logging, and Context once per process.
# #     """
# #     global GW_DB_POOL, GW_CONTEXT
# #
# #     # 1. Setup Logging
# #     initialize_worker_logger(log_level, log_file_path)
# #     # Logger for the init phase itself
# #     logger = get_station_logger("Worker Init")
# #     logger.debug(f"Worker process started (PID: {os.getpid()})")
# #
# #     # 2. Setup DB Pool
# #     try:
# #         GW_DB_POOL = DBPool(**db_credentials)
# #         logger.debug("Worker DB Pool initialized.")
# #     except Exception as e:
# #         logger.error(f"Failed to initialize Worker DB Pool: {e}")
# #         raise e
# #
# #     # 3. Handle Signals
# #     signal.signal(signal.SIGALRM, _handle_timeout)
# #
# #     # 4. Populate Context
# #     GW_CONTEXT.update({
# #         'tgl': tgl,
# #         'time0': time0,
# #         'time1': time1,
# #         'client_credentials': client_credentials,
# #         'basic_config': basic_config,
# #         'output_paths': output_paths,
# #         'pdf_trigger': pdf_trigger,
# #         'mseed_trigger': mseed_trigger,
# #         'qc_thresholds': qc_thresholds,
# #         'target_prefix': target_prefix,
# #         'accelerometer': accelerometer
# #     })
#
# # # Global Worker Resources
# # GW_CONTEXT: Dict[str, Any] = {}
# #
# #
# # def init_worker(basic_config, log_level, log_file_path, tgl, time0, time1, client_credentials, output_paths,
# #                 pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False):
# #     """
# #     Initializer for worker processes.
# #     Sets up Logging and Context once per process (CSV Mode).
# #     """
# #     global GW_CONTEXT
# #
# #     # 1. Setup Logging
# #     initialize_worker_logger(log_level, log_file_path)
# #     logger = get_station_logger("Worker Init")
# #     logger.debug(f"Worker process started (PID: {os.getpid()})")
# #
# #     # 2. Handle Signals
# #     signal.signal(signal.SIGALRM, _handle_timeout)
# #
# #     # 3. Populate Context
# #     GW_CONTEXT.update({
# #         'tgl': tgl,
# #         'time0': time0,
# #         'time1': time1,
# #         'client_credentials': client_credentials,
# #         'basic_config': basic_config,
# #         'output_paths': output_paths,
# #         'pdf_trigger': pdf_trigger,
# #         'mseed_trigger': mseed_trigger,
# #         'qc_thresholds': qc_thresholds,
# #         'target_prefix': target_prefix,
# #         'accelerometer': accelerometer
# #     })
#
#
# # Global Worker Resources
# GW_CONTEXT: Dict[str, Any] = {}
#
#
# def init_worker(basic_config, log_level, log_file_path, tgl, time0, time1, client_credentials, output_paths,
#                 pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False):
#     """
#     Initializer for worker processes.
#     Sets up Logging and Context once per process (CSV Mode).
#     """
#     global GW_CONTEXT
#
#     # 1. Setup Logging
#     initialize_worker_logger(log_level, log_file_path)
#     logger = get_station_logger("Worker Init")
#     logger.debug(f"Worker process started (PID: {os.getpid()})")
#
#     # 2. Handle Signals
#     signal.signal(signal.SIGALRM, _handle_timeout)
#
#     # 3. Populate Context
#     GW_CONTEXT.update({
#         'tgl': tgl,
#         'time0': time0,
#         'time1': time1,
#         'client_credentials': client_credentials,
#         'basic_config': basic_config,
#         'output_paths': output_paths,
#         'pdf_trigger': pdf_trigger,
#         'mseed_trigger': mseed_trigger,
#         'qc_thresholds': qc_thresholds,
#         'target_prefix': target_prefix,
#         'accelerometer': accelerometer
#     })
#
#
#
#
#
# def _handle_timeout(signum, frame):
#     """Timeout handler for worker processes."""
#     print(f"!! Process TIMEOUT after signal {signum}", flush=True)
#     raise TimeoutError("Process took too long")
#
# def process_station_data(sta_tuple):
#     """
#     This is the main worker function that runs in a separate process.
#     It processes all components (e.g., E,N,Z or 1,2,Z) for a single station.
#     """
#     global GW_DB_POOL, GW_CONTEXT
#
#     # Unpack Context
#     tgl = GW_CONTEXT['tgl']
#     time0 = GW_CONTEXT['time0']
#     time1 = GW_CONTEXT['time1']
#     client_credentials = GW_CONTEXT['client_credentials']
#     basic_config = GW_CONTEXT['basic_config']
#     output_paths = GW_CONTEXT['output_paths']
#     pdf_trigger = GW_CONTEXT['pdf_trigger']
#     mseed_trigger = GW_CONTEXT['mseed_trigger']
#     qc_thresholds = GW_CONTEXT['qc_thresholds']
#
#     try:
#         # --- UPDATED: Unpack 7 items ---
#         (network, kode, location,
#          sistem_sensor, channel_prefixes_str, channel_components_str,
#          station_sources) = sta_tuple
#
#         location = location or ''
#         # channel_prefixes = (channel_prefixes_str or '').split(',')
#         raw_prefixes = (channel_prefixes_str or '').split(',')
#         channel_components = (channel_components_str or '').split(',')
#
#
#         ###########################################
#         # --- NEW PREFIX FILTERING LOGIC ---
#         target_prefix = GW_CONTEXT.get('target_prefix')
#         is_accel = GW_CONTEXT.get('accelerometer', False)
#
#         if target_prefix:
#             # Remove spaces and force uppercase (e.g., " hH " -> "HH")
#             clean_target = target_prefix.replace(" ", "").upper()
#
#             channel_prefixes = [
#                 p.strip() for p in raw_prefixes
#                 if p.strip().upper() == clean_target
#             ]
#
#             # If the filter removes all prefixes, skip this station gracefully
#             if not channel_prefixes:
#                 logger = get_station_logger(kode)
#                 logger.info(f"Skipping {network}.{kode}: Requested prefix '{target_prefix}' not found in station's configured prefixes ({channel_prefixes_str})")
#                 return
#         else:
#             # If no --prefix flag was used, just clean up whitespace
#             channel_prefixes = [p.strip() for p in raw_prefixes if p.strip()]
#
#     except Exception as e:
#         print(f"!! FATAL: Error unpacking station tuple {sta_tuple}: {e}", flush=True)
#         return
#
#     # Use LoggerAdapter
#     logger = get_station_logger(kode)
#     logger.info(f"PROCESS START {network}.{kode} ({sistem_sensor}). Channel: {channel_prefixes}, Components: {channel_components}")
#
#     try:
#         # # --- Use Global DB Pool ---
#         # if GW_DB_POOL is None:
#         #      logger.error("Global DB Pool is not initialized!")
#         #      return
#         #
#         # repo = QCRepository(GW_DB_POOL, basic_config['use_database'])
#
#         # Resolve waveform source (station-specific or default)
#         waveform_type = basic_config.get('waveform_source', 'fdsn').lower()
#         waveform_tag = 'client' if waveform_type == 'fdsn' else 'archive'
#         waveform_source_label = f"{waveform_type} ({waveform_tag}) [default]"
#
#         if station_sources and station_sources.waveform:
#             # Use station-specific waveform source
#             waveform_type = station_sources.waveform.type
#             waveform_tag = station_sources.waveform.tag
#             waveform_source_label = f"{waveform_type} ({waveform_tag})"
#
#         # Resolve inventory source (station-specific or default)
#         inventory_type = basic_config.get('inventory_source', 'fdsn').lower()
#         inventory_tag = 'inventory_client' if inventory_type == 'fdsn' else 'inventory'
#         inventory_source_label = f"{inventory_type} ({inventory_tag}) [default]"
#
#         if station_sources and station_sources.inventory:
#             # Use station-specific inventory source
#             inventory_type = station_sources.inventory.type
#             inventory_tag = station_sources.inventory.tag
#             inventory_source_label = f"{inventory_type} ({inventory_tag})"
#
#         # Log the resolved sources
#         logger.info(f"{network}.{kode} - Waveform: {waveform_source_label}, Inventory: {inventory_source_label}")
#
#         # --- Get config settings ---
#         waveform_source = waveform_type  # Use resolved type
#         inventory_source = inventory_type  # Use resolved type
#
#         # Load station-specific or default configuration
#         from ..services.config_loader import load_client_config, load_archive_config, load_inventory_client_config, load_inventory_path_config
#
#         # Get waveform-related config
#         if waveform_source == 'fdsn':
#             waveform_client_config = load_client_config(waveform_tag)
#         elif waveform_source == 'sds':
#             # Always load from archive section
#             archive_path = load_archive_config(waveform_tag)
#
#         # Get inventory-related config
#         if inventory_source == 'fdsn':
#             if inventory_tag == 'inventory_client':
#                 # Check if there's an [inventory_client] section, otherwise use waveform client
#                 try:
#                     inventory_client_config = load_inventory_client_config(inventory_tag)
#                 except:
#                     # Fall back to waveform client if inventory_client section doesn't exist
#                     inventory_client_config = waveform_client_config if waveform_source == 'fdsn' else load_client_config('client')
#             else:
#                 inventory_client_config = load_inventory_client_config(inventory_tag)
#         elif inventory_source == 'local':
#             # Always load from inventory section
#             inventory_path = load_inventory_path_config(inventory_tag)
#
#         # --- Conditionally create FDSN client (only if needed) ---
#         fdsn_client: Optional[FDSNClient] = None
#         inventory_fdsn_client: Optional[FDSNClient] = None
#
#         if waveform_source == 'fdsn':
#             logger.debug(f"Creating FDSN client for waveforms: {waveform_tag}")
#             fdsn_client = FDSNClient(
#                 waveform_client_config['url'],
#                 user=waveform_client_config['user'],
#                 password=waveform_client_config['password']
#             )
#
#         if inventory_source == 'fdsn':
#             logger.debug(f"Creating FDSN client for inventory: {inventory_tag}")
#             # Check if same as waveform client to avoid duplicate
#             if waveform_source == 'fdsn' and inventory_tag == waveform_tag:
#                 inventory_fdsn_client = fdsn_client
#             else:
#                 inventory_fdsn_client = FDSNClient(
#                     inventory_client_config['url'],
#                     user=inventory_client_config['user'],
#                     password=inventory_client_config['password']
#                 )
#
#         # --- Create Waveform Data Client ---
#         data_client: FDSNClient | SDSClient
#         if waveform_source == 'sds':
#             if not archive_path:
#                 logger.error(f"'waveform_source' is 'sds' but archive path is not set for tag '{waveform_tag}'. Worker exiting.")
#                 return
#             data_client = SDSClient(sds_root=archive_path)
#         else:
#             if not fdsn_client:
#                 raise ConnectionError("FDSN client for waveforms was not initialized.")
#             data_client = fdsn_client  # Use FDSN client
#
#
#         # --- Validate Inventory Config ---
#         if inventory_source == 'local' and not inventory_path:
#             logger.error(f"'inventory_source' is 'local' but inventory path is not set for tag '{inventory_tag}'. Worker exiting.")
#             return
#
#     except Exception as e:
#         logger.error(f"Failed to initialize worker resources: {e}")
#         return
#
#     # Unpack output paths
#     outputmseed = output_paths['outputmseed']
#     outputsignal = output_paths['outputsignal']
#     outputPSD = output_paths['outputPSD']
#     outputPDF = output_paths['outputPDF']
#
#
# # Initialize metric collection lists
#     station_metrics_list = []
#
#     # --- UPDATED: Main Loop ---
#     for ch in channel_components:
#         id_kode = f"{kode}_{ch}_{tgl}"
#         logger.warning(f"{id_kode} - Skipped with default parameters")
#
#         # def log_default_and_continue(base_metrics=None, cha=ch, reason=""):
#         #     if base_metrics:
#         #         metrics = base_metrics
#         #     else:
#         #         metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}
#         #
#         #     try:
#         #         repo.check_and_delete_qc_detail(id_kode, tgl)
#         #         repo.insert_default_qc_detail(id_kode, kode, tgl, cha, metrics)
#         #         logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
#         #     except Exception as e:
#         #         logger.error(f"{id_kode} - FAILED to log default parameters: {e}")
#         #     time.sleep(0.5)
#
#         # def log_default_and_continue(base_metrics=None, cha=ch, reason=""):
#         #     if base_metrics:
#         #         metrics = base_metrics
#         #     else:
#         #         metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}
#         #
#         #     # Create a full dictionary of default values to prevent KeyError in qc_analyzer
#         #     default_full_metrics = {
#         #         'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
#         #         **metrics,
#         #         'pctH': '0', 'pctL': '0', 'dcl': '0', 'dcg': '0',
#         #         'long_period': '0', 'microseism': '0', 'short_period': '0'
#         #     }
#
#         def log_default_and_continue(base_metrics=None, cha=ch, reason=""):
#             if base_metrics:
#                 metrics = base_metrics
#             else:
#                 metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}
#
#             # Create a full dictionary of default values to prevent KeyError in qc_analyzer
#             default_full_metrics = {
#                 'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
#                 **metrics,
#                 'pctH': '0', 'pctL': '0', 'dcl': '0', 'dcg': '0',
#                 'long_period': '0', 'microseism': '0', 'short_period': '0'
#             }
#
#             station_metrics_list.append(default_full_metrics)
#             logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
#             time.sleep(0.5)
#
#             station_metrics_list.append(default_full_metrics)
#             logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
#             time.sleep(0.5)
#
#         # --- 2. Load/Download Waveforms ---
#         logger.debug(f"{id_kode} Acquiring waveforms (method: {waveform_source})...")
#         sig = None
#
#         try:
#             if waveform_source == 'sds':
#                 sig = sds.get_waveforms(
#                     cast(SDSClient, data_client), # Cast for Pylance
#                     network, kode, location,
#                     channel_prefixes, time0, time1, ch
#                 )
#             else: # 'fdsn' or default
#                 if not fdsn_client:
#                      raise ConnectionError("FDSN client was not initialized (check config).")
#
#                 logger.error(f"!! {ch} {channel_prefixes}ch!")
#                 sig = fdsn.get_waveforms(
#                     fdsn_client, network, kode, location,
#                     channel_prefixes, time0, time1, ch
#                 )
#
#                 logger.info(f"{sig}   {channel_prefixes}  {kode}  {location}   {ch}")
#
#         except TimeoutError:
#             logger.error(f"!! {id_kode} FDSN download timeout!")
#             log_default_and_continue(reason="Download Timeout")
#             continue
#         except Exception as e:
#             logger.error(f"!! {id_kode} data acquisition error: {e}")
#             log_default_and_continue(reason="Data Acquisition Error")
#             continue
#
# # #####################################################
#
#
#
# # # --- UPDATED: Main Loop ---
# #     for ch in channel_components:
# #         for prefix in channel_prefixes:
# #             # Combine them right away so we process them completely independently
# #             channel_code = f"{prefix}{ch}"
#
# #             # Update id_kode to use channel_code so DB entries don't overwrite each other
# #             id_kode = f"{kode}_{channel_code}_{tgl}"
# #             logger.warning(f"{id_kode} - Skipped with default parameters")
#
# #             def log_default_and_continue(base_metrics=None, cha=channel_code, reason=""):
# #                 if base_metrics:
# #                     metrics = base_metrics
# #                 else:
# #                     metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}
#
# #                 try:
# #                     repo.check_and_delete_qc_detail(id_kode, tgl)
# #                     repo.insert_default_qc_detail(id_kode, kode, tgl, cha, metrics)
# #                     logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
# #                 except Exception as e:
# #                     logger.error(f"{id_kode} - FAILED to log default parameters: {e}")
# #                 time.sleep(0.5)
#
# #             # --- 2. Load/Download Waveforms ---
# #             logger.debug(f"{id_kode} Acquiring waveforms (method: {waveform_source})...")
# #             sig = None
#
# #             try:
# #                 if waveform_source == 'sds':
# #                     sig = sds.get_waveforms(
# #                         cast(SDSClient, data_client), # Cast for Pylance
# #                         network, kode, location,
# #                         [prefix], time0, time1, ch # <-- Pass prefix as a list of 1 so SDS doesn't break
# #                     )
# #                 else: # 'fdsn' or default
# #                     if not fdsn_client:
# #                          raise ConnectionError("FDSN client was not initialized (check config).")
#
# #                     logger.error(f"!! {ch} {prefix}ch!")
#
# #                     # Notice we are now calling it with the single channel_code
# #                     sig = fdsn.get_waveforms(
# #                         fdsn_client, network, kode, location,
# #                         channel_code, time0, time1
# #                     )
#
# #                     logger.info(f"{sig}   {channel_code}  {kode}  {location}   {ch}")
#
# #             except TimeoutError:
# #                 logger.error(f"!! {id_kode} FDSN download timeout!")
# #                 log_default_and_continue(reason="Download Timeout")
# #                 continue
# #             except Exception as e:
# #                 logger.error(f"!! {id_kode} data acquisition error: {e}")
# #                 log_default_and_continue(reason="Data Acquisition Error")
# #                 continue
#
# #             # ... (The rest of your code block stays exactly the same, just indented once) ...
# # #####################################################
#
#
#         if sig is None or sig.count() == 0:
#             logger.info(f"!! {id_kode} No Data found (source: {waveform_source})")
#             log_default_and_continue(reason="No Data")
#             continue
#
#         logger.debug(f"{id_kode} Waveform acquisition complete")
#
#         # --- 2b: Load/Download Inventory ---
#         logger.debug(f"{id_kode} Acquiring inventory (method: {inventory_source})...")
#         tr = cast(Trace, sig[0])
#         inv = None
#
#         if inventory_source == 'local':
#             inv = local.get_inventory(
#                 cast(str, inventory_path), tr.stats.network, tr.stats.station,
#                 tr.stats.location, tr.stats.channel, time0
#             )
#         else: # 'fdsn' or default
#             if not inventory_fdsn_client:
#                  raise ConnectionError("FDSN client for inventory was not initialized (check config).")
#             inv = fdsn.get_inventory(
#                 inventory_fdsn_client, tr.stats.network, tr.stats.station,
#                 tr.stats.location, tr.stats.channel, time0
#             )
#
#
#         if not inv:
#             logger.warning(f"!! {id_kode} Got data but NO INVENTORY (source: {inventory_source}). Skipping.")
#             log_default_and_continue(reason="No Inventory")
#             continue
#
#         # --- 3. Save Waveform & Plot ---
#         try:
#             print(dir(tr.stats))
#             signal.alarm(300) # 3 min timeout
#             cha = tr.stats.channel
#             prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
#             comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
#             prefix_part = f"{prefix}_" if prefix else ''
#             mseed_naming_code = f"{outputmseed}/{kode}_{prefix_part}{comp}.mseed"
#             if mseed_trigger:
#                 sig.write(mseed_naming_code)
#             sig.plot(outfile=f"{outputsignal}/{kode}_{prefix_part}{comp}_signal.png")
#             signal.alarm(0)
#         except Exception as e:
#             signal.alarm(0)
#             logger.error(f"{id_kode} saving exception: {e}")
#             log_default_and_continue(cha=ch, reason="Save waveform/plot failed")
#             continue
#
#         # --- 4. Process Basic Metrics ---
#         try:
#             logger.debug(f"{id_kode} Process basic info")
#             spike_method = basic_config.get('spike_method', 'fast').lower()
#
#             metrics = basic_metrics.process_basic_metrics(
#                 sig,
#                 time0,
#                 time1,
#                 spike_method=spike_method
#             )
#
#             basic_metrics_dict = {
#                 'rms': str(round(float(metrics['rms']), 2)),
#                 'ratioamp': str(round(float(metrics['ratioamp']), 2)),
#                 'psdata': str(round(float(metrics['psdata']), 2)),
#                 'ngap': str(int(metrics['ngap'])),
#                 'nover': str(int(metrics['nover'])),
#                 'num_spikes': str(int(metrics['num_spikes']))
#             }
#
#         except Exception as e:
#             logger.error(f"{id_kode} basic info exception: {e}")
#             log_default_and_continue(cha=cha, reason="Basic metrics failed")
#             continue
#
#         # # --- 5. High Gap Check ---
#         # if int(basic_metrics_dict['ngap']) > 2000:
#         #     logger.warning(f"{id_kode} high gap ({basic_metrics_dict['ngap']}) - Continuing with default")
#         #     log_default_and_continue(basic_metrics_dict, cha, reason="High gap count")
#         #     continue
#
#         # # --- 6. Process PPSD Metrics ---
#         # logger.debug(f"{id_kode} Process PPSD metrics")
#         # prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
#         # comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
#         # prefix_part = f"{prefix}_" if prefix else ''
#         # plot_filename = f"{outputPDF}/{kode}_{prefix_part}{comp}_PDF.png"
#         # npz_path = outputPSD if pdf_trigger else ''
#         #
#         # final_metrics = None
#         # try:
#         #     signal.alarm(1200) # 20 min timeout
#         #     final_metrics = ppsd_metrics.process_ppsd_metrics(
#         #         sig,
#         #         inv,
#         #         plot_filename=plot_filename,
#         #         npz_output_path=npz_path,
#         #         is_accelerometer=is_accel
#         #     )
#         #     signal.alarm(0)
#         # except TimeoutError:
#         #     signal.alarm(0)
#         #     logger.error(f"{id_kode} PPSD metric processing timed out")
#         #     log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing timeout")
#         #     continue
#         # except Exception as e:
#         #     signal.alarm(0)
#         #     logger.error(f"{id_kode} PPSD metric processing failed: {e}")
#         #     log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing error")
#         #     continue
#
#         # # --- 6. Process PPSD Metrics ---
#         # logger.debug(f"{id_kode} Process PPSD metrics")
#         # prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
#         # comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
#         # prefix_part = f"{prefix}_" if prefix else ''
#         # plot_filename = f"{outputPDF}/{kode}_{prefix_part}{comp}_PDF.png"
#         # npz_path = outputPSD if pdf_trigger else ''
#         #
#         # # --- NEW: Auto-detect Accelerometer by Prefix ---
#         # # Add your specific accelerometer prefixes here
#         # ACCEL_PREFIXES = ["HN", "EN", "SN", "HH"]
#         #
#         # # Use accelerometer model if the CLI flag was passed OR if the prefix is in our list
#         # current_is_accel = is_accel or (prefix.upper() in ACCEL_PREFIXES)
#         #
#         # if current_is_accel:
#         #     logger.debug(f"{id_kode} Using ACCELEROMETER PPSD model for prefix '{prefix}'")
#         #
#         # final_metrics = None
#         # try:
#         #     signal.alarm(1200)  # 20 min timeout
#         #     final_metrics = ppsd_metrics.process_ppsd_metrics(
#         #         sig,
#         #         inv,
#         #         plot_filename=plot_filename,
#         #         npz_output_path=npz_path,
#         #         is_accelerometer=current_is_accel  # Pass the dynamic variable here
#         #     )
#         #     signal.alarm(0)
#         # except TimeoutError:
#         #     signal.alarm(0)
#         #     logger.error(f"{id_kode} PPSD metric processing timed out")
#         #     log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing timeout")
#         #     continue
#         # except Exception as e:
#         #     signal.alarm(0)
#         #     logger.error(f"{id_kode} PPSD metric processing failed: {e}")
#         #     log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing error")
#         #     continue
#
#         # --- 6. Process PPSD Metrics ---
#         logger.debug(f"{id_kode} Process PPSD metrics")
#         prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
#         comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
#         prefix_part = f"{prefix}_" if prefix else ''
#         plot_filename = f"{outputPDF}/{kode}_{prefix_part}{comp}_PDF.png"
#         npz_path = outputPSD if pdf_trigger else ''
#
#         # --- NEW: Auto-detect Accelerometer by Prefix from Config ---
#         # Get the string from config (fallback to standard ones if missing)
#         accel_prefixes_str = basic_config.get('accelerometer_prefixes', 'HN')
#
#         # Clean up the string into a list of uppercase prefixes (e.g., ['HN', 'EN', 'SN', 'HH'])
#         ACCEL_PREFIXES = [p.strip().upper() for p in accel_prefixes_str.split(',') if p.strip()]
#
#         # Use accelerometer model if the CLI flag was passed OR if the prefix is in our config list
#         current_is_accel = is_accel or (prefix.upper() in ACCEL_PREFIXES)
#
#         if current_is_accel:
#             logger.debug(f"{id_kode} Using ACCELEROMETER PPSD model for prefix '{prefix}'")
#
#         final_metrics = None
#         try:
#             signal.alarm(1200)  # 20 min timeout
#             final_metrics = ppsd_metrics.process_ppsd_metrics(
#                 sig,
#                 inv,
#                 plot_filename=plot_filename,
#                 npz_output_path=npz_path,
#                 is_accelerometer=current_is_accel  # Pass the dynamic variable here
#             )
#             signal.alarm(0)
#         except TimeoutError:
#             signal.alarm(0)
#             logger.error(f"{id_kode} PPSD metric processing timed out")
#             log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing timeout")
#             continue
#         except Exception as e:
#             signal.alarm(0)
#             logger.error(f"{id_kode} PPSD metric processing failed: {e}")
#             log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing error")
#             continue
#
#         # --- 7. Check PPSD Result ---
#         if not final_metrics:
#             logger.warning(f"{id_kode} PPSD metrics returned None. Skipping with defaults.")
#             log_default_and_continue(basic_metrics_dict, cha, reason="PPSD calculation failed")
#             continue
#
#         # --- 8. Commit Full Result ---
#         # all_metrics = {
#         #     'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
#         #     **basic_metrics_dict,
#         #     **final_metrics
#         # }
#
#         all_metrics = {
#             'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
#             **basic_metrics_dict,
#             **final_metrics
#         }
#         # APPEND INSTEAD OF DB INSERT
#         station_metrics_list.append(all_metrics)
#
#         # try:
#         #     logger.debug(f"{id_kode} Saving to database")
#         #     repo.check_and_delete_qc_detail(id_kode, tgl)
#         #     repo.insert_qc_detail(all_metrics)
#         #     logger.info(f"{id_kode} Process finish")
#         #     time.sleep(0.5)
#         # except Exception as e:
#         #     logger.error(f"{id_kode} Database commit error: {e}")
#
#     # --- End of channel loop ---
#
#     # # --- 9. Run QC Analysis for this station ---
#     # logger.info(f"PROCESS FINISH. Running final analysis...")
#     # try:
#     #     if qc_thresholds is not None:
#     #         qc_analyzer.run_qc_analysis(repo, basic_config['use_database'], tgl, kode, qc_thresholds)
#     #     else:
#     #         # Fallback to defaults if not provided
#     #         qc_analyzer.run_qc_analysis(repo, basic_config['use_database'], tgl, kode)
#     # except Exception as e:
#     #     logger.error(f"QC Analysis failed for {kode}: {e}")
#
#     # time.sleep(0.5)
#
# # --- 9. Run QC Analysis (Modified) ---
#     logger.info(f"PROCESS FINISH. Running final analysis in memory...")
#     analysis_results = []
#     try:
#         from ..analysis.qc_analyzer import run_qc_analysis_csv
#         analysis_results = run_qc_analysis_csv(kode, tgl, sistem_sensor, station_metrics_list, qc_thresholds)
#     except Exception as e:
#         logger.error(f"QC Analysis failed for {kode}: {e}")
#
#     time.sleep(0.5)
#
#     # Return the collected data back to the main thread
#     return {
#         'kode': kode,  # <--- Add this line so the callback knows the station name
#         'tgl': tgl,
#         'details': station_metrics_list,
#         'analysis': analysis_results
#     }
#
#     # # --- 10. Cleanup ---
#     # del(repo)
#     # logger.debug("Worker complete.")
#
#
# ################################################################


import signal
import os
import time
import numpy as np
from obspy import UTCDateTime, Trace
from typing import Optional, cast, Dict, Any
from obspy.clients.fdsn import Client as FDSNClient
from obspy.clients.filesystem.sds import Client as SDSClient
from ..services.db_pool import DBPool
from ..services.logging_config import initialize_worker_logger, get_station_logger
from ..services.repository import QCRepository
from ..services import source_mapper
from ..analysis import qc_analyzer
from ..core import basic_metrics, ppsd_metrics, models, utils
from ..clients import fdsn, sds, local

import sys
import signal

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


def init_worker(basic_config, log_level, log_file_path, tgl, time0, time1, client_credentials, output_paths,
                pdf_trigger, mseed_trigger, qc_thresholds, target_prefix=None, accelerometer=False):
    """
    Initializer for worker processes.
    Sets up Logging and Context once per process (CSV Mode).
    """
    global GW_CONTEXT

    # 1. Setup Logging
    initialize_worker_logger(log_level, log_file_path)
    logger = get_station_logger("Worker Init")
    logger.debug(f"Worker process started (PID: {os.getpid()})")

    # 2. Handle Signals
    signal.signal(signal.SIGALRM, _handle_timeout)

    # 3. Populate Context
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
        'accelerometer': accelerometer
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

    try:
        # --- UPDATED: Unpack 7 items ---
        (network, kode, location,
         sistem_sensor, channel_prefixes_str, channel_components_str,
         station_sources) = sta_tuple

        location = location or ''
        raw_prefixes = (channel_prefixes_str or '').split(',')
        channel_components = (channel_components_str or '').split(',')

        ###########################################
        # --- NEW PREFIX FILTERING LOGIC ---
        target_prefix = GW_CONTEXT.get('target_prefix')
        is_accel = GW_CONTEXT.get('accelerometer', False)

        if target_prefix:
            # Remove spaces and force uppercase (e.g., " hH " -> "HH")
            clean_target = target_prefix.replace(" ", "").upper()

            channel_prefixes = [
                p.strip() for p in raw_prefixes
                if p.strip().upper() == clean_target
            ]

            # If the filter removes all prefixes, skip this station gracefully
            if not channel_prefixes:
                logger = get_station_logger(kode)
                logger.info(
                    f"Skipping {network}.{kode}: Requested prefix '{target_prefix}' not found in station's configured prefixes ({channel_prefixes_str})")
                return
        else:
            # If no --prefix flag was used, just clean up whitespace
            channel_prefixes = [p.strip() for p in raw_prefixes if p.strip()]

    except Exception as e:
        print(f"!! FATAL: Error unpacking station tuple {sta_tuple}: {e}", flush=True)
        return

    # Use LoggerAdapter
    logger = get_station_logger(kode)
    logger.info(
        f"PROCESS START {network}.{kode} ({sistem_sensor}). Channel: {channel_prefixes}, Components: {channel_components}")

    try:
        # Resolve waveform source (station-specific or default)
        waveform_type = basic_config.get('waveform_source', 'fdsn').lower()
        waveform_tag = 'client' if waveform_type == 'fdsn' else 'archive'
        waveform_source_label = f"{waveform_type} ({waveform_tag}) [default]"

        if station_sources and station_sources.waveform:
            # Use station-specific waveform source
            waveform_type = station_sources.waveform.type
            waveform_tag = station_sources.waveform.tag
            waveform_source_label = f"{waveform_type} ({waveform_tag})"

        # Resolve inventory source (station-specific or default)
        inventory_type = basic_config.get('inventory_source', 'fdsn').lower()
        inventory_tag = 'inventory_client' if inventory_type == 'fdsn' else 'inventory'
        inventory_source_label = f"{inventory_type} ({inventory_tag}) [default]"

        if station_sources and station_sources.inventory:
            # Use station-specific inventory source
            inventory_type = station_sources.inventory.type
            inventory_tag = station_sources.inventory.tag
            inventory_source_label = f"{inventory_type} ({inventory_tag})"

        # Log the resolved sources
        logger.info(f"{network}.{kode} - Waveform: {waveform_source_label}, Inventory: {inventory_source_label}")

        # --- Get config settings ---
        waveform_source = waveform_type  # Use resolved type
        inventory_source = inventory_type  # Use resolved type

        # Load station-specific or default configuration
        from ..services.config_loader import load_client_config, load_archive_config, load_inventory_client_config, \
            load_inventory_path_config

        # Get waveform-related config
        if waveform_source == 'fdsn':
            waveform_client_config = load_client_config(waveform_tag)
        elif waveform_source == 'sds':
            # Always load from archive section
            archive_path = load_archive_config(waveform_tag)

        # Get inventory-related config
        if inventory_source == 'fdsn':
            if inventory_tag == 'inventory_client':
                # Check if there's an [inventory_client] section, otherwise use waveform client
                try:
                    inventory_client_config = load_inventory_client_config(inventory_tag)
                except:
                    # Fall back to waveform client if inventory_client section doesn't exist
                    inventory_client_config = waveform_client_config if waveform_source == 'fdsn' else load_client_config(
                        'client')
            else:
                inventory_client_config = load_inventory_client_config(inventory_tag)
        elif inventory_source == 'local':
            # Always load from inventory section
            inventory_path = load_inventory_path_config(inventory_tag)

        # --- Conditionally create FDSN client (only if needed) ---
        fdsn_client: Optional[FDSNClient] = None
        inventory_fdsn_client: Optional[FDSNClient] = None

        if waveform_source == 'fdsn':
            logger.debug(f"Creating FDSN client for waveforms: {waveform_tag}")
            fdsn_client = FDSNClient(
                waveform_client_config['url'],
                user=waveform_client_config['user'],
                password=waveform_client_config['password']
            )

        if inventory_source == 'fdsn':
            logger.debug(f"Creating FDSN client for inventory: {inventory_tag}")
            # Check if same as waveform client to avoid duplicate
            if waveform_source == 'fdsn' and inventory_tag == waveform_tag:
                inventory_fdsn_client = fdsn_client
            else:
                inventory_fdsn_client = FDSNClient(
                    inventory_client_config['url'],
                    user=inventory_client_config['user'],
                    password=inventory_client_config['password']
                )

        # --- Create Waveform Data Client ---
        data_client: FDSNClient | SDSClient
        if waveform_source == 'sds':
            if not archive_path:
                logger.error(
                    f"'waveform_source' is 'sds' but archive path is not set for tag '{waveform_tag}'. Worker exiting.")
                return
            data_client = SDSClient(sds_root=archive_path)
        else:
            if not fdsn_client:
                raise ConnectionError("FDSN client for waveforms was not initialized.")
            data_client = fdsn_client  # Use FDSN client

        # --- Validate Inventory Config ---
        if inventory_source == 'local' and not inventory_path:
            logger.error(
                f"'inventory_source' is 'local' but inventory path is not set for tag '{inventory_tag}'. Worker exiting.")
            return

    except Exception as e:
        logger.error(f"Failed to initialize worker resources: {e}")
        return

    # Unpack output paths
    outputmseed = output_paths['outputmseed']
    outputsignal = output_paths['outputsignal']
    outputPSD = output_paths['outputPSD']
    outputPDF = output_paths['outputPDF']

    # Initialize metric collection lists
    station_metrics_list = []

    # # --- UPDATED: Main Loop ---
    # for ch in channel_components:
    #     # =====================================================================
    #     # Checkpoint 1: At the very start of your component loop
    #     # =====================================================================
    #     logger.warning(
    #         f" [DEBUG CP1 - LOOP START] Station: {kode} | Available Prefixes: '{channel_prefixes}' | Current Comp (ch): '{ch}'")
    #
    #     id_kode = f"{kode}_{ch}_{tgl}"
    #     logger.warning(f"{id_kode} - Skipped with default parameters")
    #
    #     def log_default_and_continue(base_metrics=None, cha=ch, reason=""):
    #         # =====================================================================
    #         # Checkpoint 2: Before saving to station_metrics_list (for qc_details.csv)
    #         # =====================================================================
    #         logger.warning(
    #             f" [DEBUG CP2 - SAVING DETAILS] Preparing row for qc_details.csv -> Station: {kode} | Setting 'cha' column to: '{cha}'")
    #
    #         if base_metrics:
    #             metrics = base_metrics
    #         else:
    #             metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0', 'num_spikes': '0'}
    #
    #         # Create a full dictionary of default values to prevent KeyError in qc_analyzer
    #         default_full_metrics = {
    #             'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
    #             **metrics,
    #             'pctH': '0', 'pctL': '0', 'dcl': '0', 'dcg': '0',
    #             'long_period': '0', 'microseism': '0', 'short_period': '0'
    #         }
    #
    #         station_metrics_list.append(default_full_metrics)
    #         logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
    #         time.sleep(0.5)
    #
    #     # --- 2. Load/Download Waveforms ---
    #     logger.debug(f"{id_kode} Acquiring waveforms (method: {waveform_source})...")
    #     sig = None
    #
    #     try:
    #         if waveform_source == 'sds':
    #             sig = sds.get_waveforms(
    #                 cast(SDSClient, data_client),  # Cast for Pylance
    #                 network, kode, location,
    #                 channel_prefixes, time0, time1, ch
    #             )
    #         else:  # 'fdsn' or default
    #             if not fdsn_client:
    #                 raise ConnectionError("FDSN client was not initialized (check config).")
    #
    #             logger.error(f"!! {ch} {channel_prefixes}ch!")
    #             sig = fdsn.get_waveforms(
    #                 fdsn_client, network, kode, location,
    #                 channel_prefixes, time0, time1, ch
    #             )
    #
    #             logger.info(f"{sig}   {channel_prefixes}  {kode}  {location}   {ch}")
    #
    #     except TimeoutError:
    #         logger.error(f"!! {id_kode} FDSN download timeout!")
    #         log_default_and_continue(reason="Download Timeout")
    #         continue
    #     except Exception as e:
    #         logger.error(f"!! {id_kode} data acquisition error: {e}")
    #         log_default_and_continue(reason="Data Acquisition Error")
    #         continue
    #
    #     if sig is None or sig.count() == 0:
    #         logger.info(f"!! {id_kode} No Data found (source: {waveform_source})")
    #         log_default_and_continue(reason="No Data")
    #         continue
    #
    #     logger.debug(f"{id_kode} Waveform acquisition complete")
    #
    #     # --- 2b: Load/Download Inventory ---
    #     logger.debug(f"{id_kode} Acquiring inventory (method: {inventory_source})...")
    #     tr = cast(Trace, sig[0])
    #     inv = None
    #
    #     if inventory_source == 'local':
    #         inv = local.get_inventory(
    #             cast(str, inventory_path), tr.stats.network, tr.stats.station,
    #             tr.stats.location, tr.stats.channel, time0
    #         )
    #     else:  # 'fdsn' or default
    #         if not inventory_fdsn_client:
    #             raise ConnectionError("FDSN client for inventory was not initialized (check config).")
    #         inv = fdsn.get_inventory(
    #             inventory_fdsn_client, tr.stats.network, tr.stats.station,
    #             tr.stats.location, tr.stats.channel, time0
    #         )
    #
    #     if not inv:
    #         logger.warning(f"!! {id_kode} Got data but NO INVENTORY (source: {inventory_source}). Skipping.")
    #         log_default_and_continue(reason="No Inventory")
    #         continue
    #
    #     # --- 3. Save Waveform & Plot ---
    #     try:
    #         print(dir(tr.stats))
    #         signal.alarm(300)  # 3 min timeout
    #         cha = tr.stats.channel
    #         prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
    #         comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
    #         prefix_part = f"{prefix}_" if prefix else ''
    #         mseed_naming_code = f"{outputmseed}/{kode}_{prefix_part}{comp}.mseed"
    #         if mseed_trigger:
    #             sig.write(mseed_naming_code)
    #         sig.plot(outfile=f"{outputsignal}/{kode}_{prefix_part}{comp}_signal.png")
    #         signal.alarm(0)
    #     except Exception as e:
    #         signal.alarm(0)
    #         logger.error(f"{id_kode} saving exception: {e}")
    #         log_default_and_continue(cha=ch, reason="Save waveform/plot failed")
    #         continue
    #
    #     # --- 4. Process Basic Metrics ---
    #     try:
    #         logger.debug(f"{id_kode} Process basic info")
    #         spike_method = basic_config.get('spike_method', 'fast').lower()
    #
    #         metrics = basic_metrics.process_basic_metrics(
    #             sig,
    #             time0,
    #             time1,
    #             spike_method=spike_method
    #         )
    #
    #         basic_metrics_dict = {
    #             'rms': str(round(float(metrics['rms']), 2)),
    #             'ratioamp': str(round(float(metrics['ratioamp']), 2)),
    #             'psdata': str(round(float(metrics['psdata']), 2)),
    #             'ngap': str(int(metrics['ngap'])),
    #             'nover': str(int(metrics['nover'])),
    #             'num_spikes': str(int(metrics['num_spikes']))
    #         }
    #
    #     except Exception as e:
    #         logger.error(f"{id_kode} basic info exception: {e}")
    #         log_default_and_continue(cha=cha, reason="Basic metrics failed")
    #         continue
    #
    #     # --- 6. Process PPSD Metrics ---
    #     logger.debug(f"{id_kode} Process PPSD metrics")
    #     prefix = cha[:2] if isinstance(cha, str) and len(cha) >= 2 else ''
    #     comp = cha[-1] if isinstance(cha, str) and len(cha) >= 1 else ''
    #     prefix_part = f"{prefix}_" if prefix else ''
    #     plot_filename = f"{outputPDF}/{kode}_{prefix_part}{comp}_PDF.png"
    #     npz_path = outputPSD if pdf_trigger else ''
    #
    #     # --- NEW: Auto-detect Accelerometer by Prefix from Config ---
    #     # Get the string from config (fallback to standard ones if missing)
    #     accel_prefixes_str = basic_config.get('accelerometer_prefixes', 'HN')
    #
    #     # Clean up the string into a list of uppercase prefixes (e.g., ['HN', 'EN', 'SN', 'HH'])
    #     ACCEL_PREFIXES = [p.strip().upper() for p in accel_prefixes_str.split(',') if p.strip()]
    #
    #     # Use accelerometer model if the CLI flag was passed OR if the prefix is in our config list
    #     current_is_accel = is_accel or (prefix.upper() in ACCEL_PREFIXES)
    #
    #     if current_is_accel:
    #         logger.debug(f"{id_kode} Using ACCELEROMETER PPSD model for prefix '{prefix}'")
    #
    #     final_metrics = None
    #     try:
    #         signal.alarm(1200)  # 20 min timeout
    #         final_metrics = ppsd_metrics.process_ppsd_metrics(
    #             sig,
    #             inv,
    #             plot_filename=plot_filename,
    #             npz_output_path=npz_path,
    #             is_accelerometer=current_is_accel  # Pass the dynamic variable here
    #         )
    #         signal.alarm(0)
    #     except TimeoutError:
    #         signal.alarm(0)
    #         logger.error(f"{id_kode} PPSD metric processing timed out")
    #         log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing timeout")
    #         continue
    #     except Exception as e:
    #         signal.alarm(0)
    #         logger.error(f"{id_kode} PPSD metric processing failed: {e}")
    #         log_default_and_continue(basic_metrics_dict, cha, reason="PPSD processing error")
    #         continue
    #
    #     # --- 7. Check PPSD Result ---
    #     if not final_metrics:
    #         logger.warning(f"{id_kode} PPSD metrics returned None. Skipping with defaults.")
    #         log_default_and_continue(basic_metrics_dict, cha, reason="PPSD calculation failed")
    #         continue
    #
    #     # --- 8. Commit Full Result ---
    #     all_metrics = {
    #         'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
    #         **basic_metrics_dict,
    #         **final_metrics
    #     }
    #     # APPEND INSTEAD OF DB INSERT
    #     station_metrics_list.append(all_metrics)

#########################################################
#######################################################################

    # Initialize metric collection lists
    station_metrics_list = []

    # --- UPDATED: Nested Loop (Prefixes x Components) ---
    for prefix in channel_prefixes:
        for ch in channel_components:
            # Combine them right away into a full 3-letter code (e.g., "SHE", "HNE")
            cha = f"{prefix}{ch}"
            id_kode = f"{kode}_{cha}_{tgl}"

            # =====================================================================
            # Checkpoint 1: Loop Start
            # =====================================================================
            logger.warning(f" [DEBUG CP1 - LOOP START] Station: {kode} | Target Channel (cha): '{cha}'")

            logger.warning(f"{id_kode} - Skipped with default parameters")

            def log_default_and_continue(base_metrics=None, cha=cha, reason=""):
                # =====================================================================
                # Checkpoint 2: Saving Details
                # =====================================================================
                logger.warning(f" [DEBUG CP2 - SAVING DETAILS] Station: {kode} | Setting 'cha' column to: '{cha}'")

                if base_metrics:
                    metrics = base_metrics
                else:
                    metrics = {'rms': '0', 'ratioamp': '0', 'psdata': '0', 'ngap': '1', 'nover': '0',
                               'num_spikes': '0'}

                default_full_metrics = {
                    'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
                    **metrics,
                    'pctH': '0', 'pctL': '0', 'dcl': '0', 'dcg': '0',
                    'long_period': '0', 'microseism': '0', 'short_period': '0'
                }

                station_metrics_list.append(default_full_metrics)
                logger.warning(f"{id_kode} - Skipped with default parameters. Reason: {reason}")
                time.sleep(0.5)

            # --- 2. Load/Download Waveforms ---
            logger.debug(f"{id_kode} Acquiring waveforms (method: {waveform_source})...")
            sig = None

            try:
                if waveform_source == 'sds':
                    # PASS ONLY A SINGLE PREFIX IN THE LIST SO SDS CAN BUILD THE EXACT PATH
                    sig = sds.get_waveforms(
                        cast(SDSClient, data_client),
                        network, kode, location,
                        [prefix], time0, time1, ch
                    )
                else:  # 'fdsn' or default
                    if not fdsn_client:
                        raise ConnectionError("FDSN client was not initialized (check config).")

                    # PASS THE EXACT 3-LETTER CHANNEL STRING
                    sig = fdsn.get_waveforms(
                        fdsn_client, network, kode, location,
                        cha, time0, time1
                    )

            except TimeoutError:
                logger.error(f"!! {id_kode} download timeout!")
                log_default_and_continue(reason="Download Timeout")
                continue
            except Exception as e:
                logger.error(f"!! {id_kode} data acquisition error: {e}")
                log_default_and_continue(reason="Data Acquisition Error")
                continue

            if sig is None or sig.count() == 0:
                logger.info(f"!! {id_kode} No Data found (source: {waveform_source})")
                log_default_and_continue(reason="No Data")
                continue

            logger.debug(f"{id_kode} Waveform acquisition complete")

            # --- 2b: Load/Download Inventory ---
            logger.debug(f"{id_kode} Acquiring inventory (method: {inventory_source})...")
            tr = cast(Trace, sig[0])
            inv = None

            if inventory_source == 'local':
                inv = local.get_inventory(
                    cast(str, inventory_path), tr.stats.network, tr.stats.station,
                    tr.stats.location, tr.stats.channel, time0
                )
            else:  # 'fdsn' or default
                if not inventory_fdsn_client:
                    raise ConnectionError("FDSN client for inventory was not initialized (check config).")
                inv = fdsn.get_inventory(
                    inventory_fdsn_client, tr.stats.network, tr.stats.station,
                    tr.stats.location, tr.stats.channel, time0
                )

            if not inv:
                logger.warning(f"!! {id_kode} Got data but NO INVENTORY (source: {inventory_source}). Skipping.")
                log_default_and_continue(reason="No Inventory")
                continue

            # --- 3. Save Waveform & Plot ---
            try:
                signal.alarm(300)  # 3 min timeout
                prefix_part = f"{prefix}_" if prefix else ''
                mseed_naming_code = f"{outputmseed}/{kode}_{prefix_part}{ch}.mseed"
                if mseed_trigger:
                    sig.write(mseed_naming_code)
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

                metrics = basic_metrics.process_basic_metrics(
                    sig,
                    time0,
                    time1,
                    spike_method=spike_method
                )

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

            if current_is_accel:
                logger.debug(f"{id_kode} Using ACCELEROMETER PPSD model for prefix '{prefix}'")

            final_metrics = None
            try:
                signal.alarm(1200)  # 20 min timeout
                final_metrics = ppsd_metrics.process_ppsd_metrics(
                    sig,
                    inv,
                    plot_filename=plot_filename,
                    npz_output_path=npz_path,
                    is_accelerometer=current_is_accel
                )
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

            # --- 7. Check PPSD Result ---
            if not final_metrics:
                logger.warning(f"{id_kode} PPSD metrics returned None. Skipping with defaults.")
                log_default_and_continue(basic_metrics_dict, cha=cha, reason="PPSD calculation failed")
                continue

            # --- 8. Commit Full Result ---
            all_metrics = {
                'id_kode': id_kode, 'kode': kode, 'tgl': tgl, 'cha': cha,
                **basic_metrics_dict,
                **final_metrics
            }
            station_metrics_list.append(all_metrics)

    # --- End of nested channel loop ---

##################++++


    # --- End of channel loop ---

    # --- 9. Run QC Analysis (Modified) ---
    logger.info(f"PROCESS FINISH. Running final analysis in memory...")

    # =====================================================================
    # Checkpoint 3: Before passing to QC Analyzer (for qc_analysis.csv)
    # =====================================================================
    logger.warning(
        f" [DEBUG CP3 - ANALYZER INPUT] Total rows going into run_qc_analysis_csv: {len(station_metrics_list)}")
    for idx, row in enumerate(station_metrics_list):
        logger.warning(f"   -> Row [{idx}] has 'cha' value: '{row.get('cha')}'")
    # =====================================================================

    analysis_results = []
    try:
        from ..analysis.qc_analyzer import run_qc_analysis_csv
        analysis_results = run_qc_analysis_csv(kode, tgl, sistem_sensor, station_metrics_list, qc_thresholds)
    except Exception as e:
        logger.error(f"QC Analysis failed for {kode}: {e}")

    time.sleep(0.5)

    # Return the collected data back to the main thread
    return {
        'kode': kode,  # <--- Add this line so the callback knows the station name
        'tgl': tgl,
        'details': station_metrics_list,
        'analysis': analysis_results
    }
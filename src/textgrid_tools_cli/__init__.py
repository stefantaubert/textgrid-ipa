from textgrid_tools_cli.globals import ExecutionResult, Success
from textgrid_tools_cli.grid import (get_audio_synchronization_parser,
                                     get_creation_parser)
from textgrid_tools_cli.grid import \
    get_splitting_parser as get_grid_splitting_parser
from textgrid_tools_cli.grid import get_stats_generation_parser
from textgrid_tools_cli.grids import (get_dictionary_creation_parser,
                                      get_grids_plot_interval_durations_parser,
                                      get_marks_exporting_parser)
from textgrid_tools_cli.intervals import (get_between_pause_joining_parser,
                                          get_boundary_fixing_parser,
                                          get_boundary_joining_parser,
                                          get_duration_joining_parser,
                                          get_mark_joining_parser,
                                          get_plot_interval_durations_parser)
from textgrid_tools_cli.intervals import \
    get_removing_parser as get_intervals_removing_parser
from textgrid_tools_cli.intervals import get_sentence_joining_parser
from textgrid_tools_cli.intervals import \
    get_splitting_parser as get_intervals_splitting_parser
from textgrid_tools_cli.intervals import (get_splitting_v2_parser,
                                          get_symbols_joining_parser)
from textgrid_tools_cli.tier import (get_cloning_parser, get_copying_parser,
                                     get_mapping_parser, get_moving_parser,
                                     get_renaming_parser,
                                     get_text_conversion_parser)
from textgrid_tools_cli.tiers import (get_arpa_to_ipa_transcription_parser,
                                      get_label_silence_parser,
                                      get_normalization_parser)
from textgrid_tools_cli.tiers import \
    get_removing_parser as get_tiers_removing_parser
from textgrid_tools_cli.tiers import (get_string_format_switching_parser,
                                      get_symbol_removing_parser,
                                      get_transcription_parser)
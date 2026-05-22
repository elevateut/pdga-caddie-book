"""pdga-caddie-book — generate caddie books for PDGA-sanctioned disc golf tournaments.

Public API:
  - pdga.fetch_layouts(tournament_id) — pull canonical layouts from PDGA TM
  - builder.build_event(event_yaml_path, output_dir) — render full caddie book set
  - scorecards.build_event(event_yaml_path, output_dir) — render printable scorecards
"""

__version__ = "0.1.0"

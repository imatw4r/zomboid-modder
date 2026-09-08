import argparse

from zomboid_modder.ui.tui.app import ZomboidModderApp


def main() -> None:
    parser = argparse.ArgumentParser(prog="zomboid-modder")
    parser.add_argument("--profile", help="Profile name to load on startup")
    parser.add_argument("--config", help="Path to config.toml (overrides default)")
    args = parser.parse_args()

    app = ZomboidModderApp(profile_name=args.profile, config_path=args.config)
    app.run()

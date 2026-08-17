"""PyRoboSimulator CLI"""
import argparse
from .cli_dashboard import PyRoboSimulatorDashboard

def main():
    parser = argparse.ArgumentParser(description='PyRoboSimulator World Engine')
    subparsers = parser.add_subparsers(dest='command')
    dashboard_parser = subparsers.add_parser('dashboard', help='View dashboard')
    dashboard_parser.add_argument('--static', action='store_true')
    dashboard_parser.add_argument('--export', type=str)
    args = parser.parse_args()
    
    if args.command == 'dashboard':
        dashboard = PyRoboSimulatorDashboard()
        if args.export:
            dashboard.export_json(args.export)
        else:
            dashboard.run_dashboard(interactive=not args.static)

if __name__ == '__main__':
    main()

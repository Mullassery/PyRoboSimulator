"""Post-install messaging for PyRoboSimulator"""


def post_install():
    from pyrobosimulator import __version__

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ PyRoboSimulator v{__version__} installed successfully!

📌 WHAT IS THIS?
   A Rust-core world/agent data model (World, Agent, Mission) exposed to
   Python via PyO3, plus a real ROS 2/Gazebo SDF world exporter
   (ROS2Bridge). This package is the lightweight core library; the
   full FastAPI simulation backend (REST API, sensor suite, physics
   backends) lives separately in this repo's backend/ directory.

🚀 GET STARTED (Copy & Paste):
   $ python3 -c "
from pyrobosimulator import World, Agent, AgentType
w = World('my_world')
w.add_agent(Agent('robot1', AgentType.Robot))
print(f'World {{w.name()}} has {{w.agent_count()}} agent(s)')
"
   $ pyrobosimulator dashboard --static

📖 DOCUMENTATION:
   Tutorials:     https://github.com/Mullassery/PyRoboSimulator#readme
   GitHub Issues: https://github.com/Mullassery/PyRoboSimulator/issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


if __name__ == "__main__":
    post_install()

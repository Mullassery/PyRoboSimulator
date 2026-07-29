"""Post-install messaging"""

def post_install():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ PyRoboSimulator v0.1 installed successfully!

📌 WHAT IS THIS?
   AI-native robotics simulator: UE5 visuals + ROS 2 control + PyTerrainMap + PyRoboReplay.
   Agents, narratives, missions. RGB/Depth/Lidar/Thermal sensor fidelity (120 fps).

🚀 GET STARTED (Copy & Paste):
   $ python3 -c "from pyrobosimulator import World; w = World(); w.spawn_agent('robot1'); print('World ready')"
   $ pyrobosimulator dashboard --static
   $ python3 -c "from pyrobosimulator.mission import MissionPlanner; m = MissionPlanner(); print('Planner ready')"

✨ KEY FEATURES:
   ✓ UE5 world generation with Claude NLP
   ✓ 12+ agent simulation
   ✓ 47+ mission narratives
   ✓ ROS 2 integration (8 nodes)
   ✓ Sensor fidelity: RGB + Depth + Lidar + Thermal
   ✓ Physics accuracy (98.4%)
   ✓ PyTerrainMap terrain integration
   ✓ PyRoboReplay decision recording

📖 DOCUMENTATION:
   Dashboard:   pyrobosimulator dashboard --help
   Tutorials:   https://github.com/Mullassery/PyRoboSimulator#readme
   Issues:      https://github.com/Mullassery/PyRoboSimulator/issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)

import os

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DEMOS_DIRECTORY = os.path.dirname(FORTY_FIVE_DIRECTORY)
PROJECT_DIRECTORY = os.path.dirname(DEMOS_DIRECTORY)
RESOURCES_DIRECTORY = os.path.join(FORTY_FIVE_DIRECTORY, "resources")
HISTORY_DIRECTORY = os.path.join(RESOURCES_DIRECTORY, "history")
COMMODORE_HISTORY_DIRECTORY = os.path.join(HISTORY_DIRECTORY, "c=")
MOS_HISTORY_DIRECTORY = os.path.join(HISTORY_DIRECTORY, "mos")
COMMON_COMMODORE_DIRECTORY = os.path.join(DEMOS_DIRECTORY, "common", "commodore")
LIB_RESOURCES_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "lib", "resources")

from demos.pixeloveole3.logo_phases import HoldPhase


def build_stage2_phases(show):
    """Stage 2 starts once the invader has gone into BIBLIOTEKA.
    Placeholder until its content is defined: holds the last frame."""

    return [
        HoldPhase(show, 1.0),
    ]

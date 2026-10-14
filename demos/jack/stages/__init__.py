from demos.jack.stages import atari, commodore, last_years, typewriters, war_years

CHAPTERS = (war_years.CHAPTER, typewriters.CHAPTER, commodore.CHAPTER, atari.CHAPTER, last_years.CHAPTER)


def build_stages(album):
    return [stage for chapter in CHAPTERS for stage in chapter.build(album)]

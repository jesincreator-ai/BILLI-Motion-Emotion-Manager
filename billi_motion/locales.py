"""Tiny offline UI phrase table. Display fonts must include Tamil/Sinhala glyphs."""

TEXT = {
    "en": {"neutral": "Neutral", "happy": "Happy", "sad": "Sad", "angry": "Angry",
           "curious": "Curious", "surprised": "Surprised", "sleepy": "Sleepy",
           "speaking": "Speaking", "silent": "Silent"},
    "ta": {"neutral": "சாதாரணம்", "happy": "மகிழ்ச்சி", "sad": "சோகம்", "angry": "கோபம்",
           "curious": "ஆர்வம்", "surprised": "ஆச்சரியம்", "sleepy": "தூக்கம்",
           "speaking": "பேசுகிறது", "silent": "அமைதி"},
    "si": {"neutral": "සාමාන්‍ය", "happy": "සතුටුයි", "sad": "දුකයි", "angry": "කෝපයි",
           "curious": "කුතුහලය", "surprised": "පුදුමයි", "sleepy": "නිදිමතයි",
           "speaking": "කතා කරයි", "silent": "නිහඬයි"},
}


def phrase(key, language="en"):
    table = TEXT.get(language, TEXT["en"])
    return table.get(key, TEXT["en"].get(key, key))

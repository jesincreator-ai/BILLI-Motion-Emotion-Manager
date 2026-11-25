"""Tiny offline UI phrase table. Display fonts must include Tamil/Sinhala glyphs."""

TEXT = {
    "en": {
        "neutral": "Neutral",
        "happy": "Happy",
        "sad": "Sad",
        "surprise": "Surprise",
        "disappointment": "Disappointed",
        "sorry": "Sorry",
        "crying": "Crying",
        "angry": "Angry",
        "ego_fire": "Ego Fire",
        "speaking": "Speaking",
        "silent": "Silent",
    },
    "ta": {
        "neutral": "சாதாரணம்",
        "happy": "மகிழ்ச்சி",
        "sad": "சோகம்",
        "surprise": "ஆச்சரியம்",
        "disappointment": "ஏமாற்றம்",
        "sorry": "மன்னிக்கவும்",
        "crying": "அழுகிறது",
        "angry": "கோபம்",
        "ego_fire": "தீவிர ஆவேசம்",
        "speaking": "பேசுகிறது",
        "silent": "அமைதி",
    },
    "si": {
        "neutral": "සාමාන්‍ය",
        "happy": "සතුට",
        "sad": "දුක",
        "surprise": "පුදුමය",
        "disappointment": "කලකිරීම",
        "sorry": "සමාවන්න",
        "crying": "අඬනවා",
        "angry": "කෝපය",
        "ego_fire": "අග්නි ආවේගය",
        "speaking": "කතා කරයි",
        "silent": "නිහඬයි",
    },
}


def phrase(key, language="en"):
    # Preserve the older display label used by integrations before the
    # canonical emotion spelling changed from "surprised" to "surprise".
    if key == "surprised":
        key = "surprise"
    table = TEXT.get(language, TEXT["en"])
    return table.get(key, TEXT["en"].get(key, key))

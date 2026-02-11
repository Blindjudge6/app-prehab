import re
import unittest

from prehab_logic import QUESTIONS, EXERCISE_LIBRARY, iter_patient_texts


class TestReadability(unittest.TestCase):
    def test_question_count_is_fixed(self):
        self.assertEqual(len(QUESTIONS), 7)

    def test_exercise_fields_are_complete(self):
        required_fields = {"name", "how", "focus", "safety"}
        for level_data in EXERCISE_LIBRARY.values():
            for section in ["warmup", "strength", "balance", "cooldown"]:
                for exercise in level_data[section]:
                    self.assertTrue(required_fields.issubset(exercise.keys()))
                    for field in required_fields:
                        self.assertTrue(isinstance(exercise[field], str) and exercise[field].strip())
            self.assertTrue(required_fields.issubset(level_data["endurance"].keys()))

    def test_patient_texts_are_readable(self):
        texts = [text.strip() for text in iter_patient_texts() if text and text.strip()]
        self.assertGreater(len(texts), 20)

        for text in texts:
            words = re.findall(r"[A-Za-zÄÖÜäöüß0-9\-]+", text)
            self.assertLessEqual(len(text), 140, msg=f"Text zu lang: {text}")
            self.assertLessEqual(len(words), 22, msg=f"Zu viele Wörter: {text}")

        avg_words = sum(len(re.findall(r"[A-Za-zÄÖÜäöüß0-9\-]+", t)) for t in texts) / len(texts)
        self.assertLessEqual(avg_words, 11.5, msg=f"Durchschnitt zu komplex: {avg_words:.2f} Wörter")


if __name__ == "__main__":
    unittest.main()

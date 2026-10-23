"""The diagnostic accepts the activity opt-in used by native hooks."""
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('activity_doctor', Path(__file__).with_name('doctor.py'))
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class ActivityConfiguration(unittest.TestCase):
    def test_activity_boolean_is_known_without_warning(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                self.assertEqual(doctor._dev_valida_sesion({'actividad': enabled}), [])

    def test_invalid_activity_is_an_error_with_a_boolean_remedy(self):
        for value in (None, 0, 1, 'true', {}, []):
            with self.subTest(value=value):
                rows = doctor._dev_valida_sesion({'actividad': value})
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['estado'], doctor.ERROR)
                self.assertEqual(rows[0]['que'], 'dev.json `sesion.actividad`')
                self.assertIn('"actividad": true', rows[0]['arreglo'])

    def test_invalid_session_remedy_keeps_activity_opt_in_disabled(self):
        rows = doctor._dev_valida_sesion('true')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['estado'], doctor.ERROR)
        self.assertIn('"actividad": false', rows[0]['arreglo'])


if __name__ == '__main__':
    unittest.main()

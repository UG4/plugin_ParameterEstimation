import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
import numpy as np
from UGParameterEstimator import ErroredEvaluation, GenericEvaluation

class GenericEvaluationTests(unittest.TestCase):

    def setUp(self):
        with open("0_measurement.json", "w") as f:
            f.write("""
            {
                "metadata": {
                    "finished": true
                },
                "data": [
                    {
                        "time": 1,
                        "value": 1
                    },
                    {
                        "time": 2,
                        "value": 2
                    },
                    {
                        "time": 3,
                        "value": 2
                    },
                    {
                        "time": 4,
                        "value": 1
                    },
                    {
                        "time": 5,
                        "value": 0
                    }
                ]
            }            
            """)

        with open("1_measurement.json", "w") as f:
            f.write("""
            {
                "metadata": {
                    "finished": true
                },
                "data": [
                    {
                        "time": 1.5,
                        "value": 1.5
                    },
                    {
                        "time": 2.5,
                        "value": 2.5
                    },
                    {
                        "time": 3.5,
                        "value": 1.5
                    },
                    {
                        "time": 4,
                        "value": 1
                    }
                ]
            }            
            """)

        self.series0 = GenericEvaluation.parse(".", 0)
        self.series1 = GenericEvaluation.parse(".", 1)

        if isinstance(self.series0, ErroredEvaluation):
            print(self.series0.reason)
        
        if isinstance(self.series1, ErroredEvaluation):
            print(self.series1.reason)

    def tearDown(self):

        os.remove("0_measurement.json")
        os.remove("1_measurement.json")

    def test_read_in(self):
        self.assertEqual(self.series0.times, [1, 2, 3, 4, 5])
        self.assertEqual(self.series1.times, [1.5, 2.5, 3.5, 4])
        self.assertEqual(self.series0.data, [1, 2, 2, 1, 0])
        self.assertEqual(self.series1.data, [1.5, 2.5, 1.5, 1])

    def test_numpy_array(self):
        self.assertTrue(np.allclose(
            self.series0.getNumpyArray(), 
            np.array([1, 2, 2, 1, 0])))

        self.assertTrue(np.allclose(
            self.series1.getNumpyArray(), 
            np.array([1.5, 2.5, 1.5, 1])))

    def test_numpy_array_like(self):
        self.assertTrue(np.allclose(
            self.series1.getNumpyArrayLike(self.series0),
            np.array([1.5, 2, 2, 1, 1])))

        self.assertTrue(np.allclose(
            self.series0.getNumpyArrayLike(self.series1),
            np.array([1.5, 2, 1.5, 1])))

    def test_numpy_array_like_same_format(self):
        self.assertTrue(np.allclose(
            self.series1.getNumpyArrayLike(self.series1),
            np.array([1.5, 2.5, 1.5, 1])))

if __name__ == '__main__':
    unittest.main()
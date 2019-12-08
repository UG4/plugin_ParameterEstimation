import unittest
import os
import numpy as np
from UGParameterEstimator import FreeSurfaceTimeDependentEvaluation

class FreeSurfaceTimeDependentEvaluationTests(unittest.TestCase):

    def setUp(self):
        with open("0_measurement.txt","w") as f:
            f.write("1\t0\t1\n")
            f.write("1\t2\t2\n")
            f.write("2\t0\t2\n")
            f.write("2\t2\t3\n")
            f.write("3\t0\t3\n")
            f.write("3\t2\t4\n")
            f.write("FINISHED")
        self.series = FreeSurfaceTimeDependentEvaluation.parse(".", 0)

        with open("1_measurement.txt","w") as f:
            f.write("1\t0\t1\n")
            f.write("1\t2\t2\n")
            f.write("1.5\t0\t2\n")
            f.write("1.5\t2\t3\n")
            f.write("2.5\t0\t3\n")
            f.write("2.5\t2\t4\n")
            f.write("3.5\t0\t4\n")
            f.write("3.5\t2\t5\n")
            f.write("FINISHED")
        self.series2 = FreeSurfaceTimeDependentEvaluation.parse(".", 1)

        os.remove("0_measurement.txt")
        os.remove("1_measurement.txt")

    def test_read_in(self):
        self.assertEqual(self.series.locations, [0,2])
        self.assertEqual(self.series.times, [1,2,3])
        self.assertEqual(self.series.data, [[1,2],[2,3],[3,4]])

    def test_numpy_array(self):
        self.assertTrue(np.allclose(self.series.getNumpyArray(),np.array([1,2,2,3,3,4])))

    def test_numpy_array_like(self):
        self.assertTrue(np.allclose(self.series2.getNumpyArrayLike(self.series),np.array([1,2,2.5,3.5,3.5,4.5])))

    def test_numpy_array_like_2(self):
        self.assertTrue(np.allclose(self.series.getNumpyArrayLike(self.series2),np.array([1,2,1.5,2.5,2.5,3.5,2.5,3.5])))

    def test_numpy_array_like_same_format(self):
        self.assertTrue(np.allclose(self.series.getNumpyArrayLike(self.series),np.array([1,2,2,3,3,4])))

if __name__ == '__main__':
    unittest.main()
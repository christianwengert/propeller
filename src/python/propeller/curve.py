from math import atan2
from typing import List


class PiecewiseLinearCurve:

    def __init__(self, points: List[(float, float)], smoothing_distance: float = 0.0):

        if len(points) < 2:
            raise ValueError('must provide at least two points')

        self._smoothing_distance = smoothing_distance
        self._points = points[:]
        self._points.sort(key=lambda p: p[0])

    def _clamp_x(self, value: float) -> float:

        return max(self._points[0][0], min(value, self._points[-1][0]))

    def _get_points_of_segment_containing(self, x):

        x = self._clamp_x(x)   # effectively extends the curve to +- infinity

        for i in range(len(self._points)):
            if x <= self._points[i][0]:
                return self._points[i], self._points[i + 1]

        raise Exception('this should not happen')

    def _get_y(self, x: float) -> float:

        (x1, y1), (x2, y2) = self._get_points_of_segment_containing(x)

        _x = x - x1

        dx = x2 - x1
        dy = y2 - y1

        m = dy/dx

        return _x * m + y1

    def get_slope_angle(self, x: float, dx=0.1) -> float:

        x1 = x - dx
        x2 = x + dx

        y1 = self[x1]
        y2 = self[x2]

        return atan2(y2-y1, x2-x1)

    def get_slope(self, x: float, dx=0.1) -> float:

        x1 = x - dx
        x2 = x + dx

        y1 = self[x1]
        y2 = self[x2]

        return (y2 - y1)/(x2 - x1)

    def __getitem__(self, x: float) -> float:

        if self._smoothing_distance == 0:
            return self._get_y(x)

        y1 = self._get_y(x - self._smoothing_distance)
        y2 = self._get_y(x + self._smoothing_distance)

        return (y1 + y2) / 2.0
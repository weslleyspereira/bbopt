"""TODO: <one line to give the program's name and a brief idea of what it does.>
"""

# Copyright (C) 2023 National Renewable Energy Laboratory

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__authors__ = ["Weslley S. Pereira"]
__contact__ = "weslley.dasilvapereira@nrel.gov"
__maintainer__ = "Weslley S. Pereira"
__email__ = "weslley.dasilvapereira@nrel.gov"
__credits__ = ["Weslley S. Pereira"]
__version__ = "0.1.0"
__deprecated__ = False

import numpy as np
import sys
from blackboxopt.rbf import *


class TestRbfModel:
    rbf_model = RbfModel()

    def test_phi(self):
        self.rbf_model.type = RbfType.LINEAR
        r_linear = np.array([1.0, 2.0, 3.0])
        result_linear = self.rbf_model.phi(r_linear)
        expected_linear = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_equal(np.array(result_linear), expected_linear)
        assert self.rbf_model.phi(4.0) == 4.0

        self.rbf_model.type = RbfType.CUBIC
        r_cubic = np.array([1.0, 2.0, 3.0])
        result_cubic = self.rbf_model.phi(r_cubic)
        expected_cubic = np.array([1.0, 8.0, 27.0])
        np.testing.assert_array_equal(np.array(result_cubic), expected_cubic)
        assert self.rbf_model.phi(4.0) == 64.0

        self.rbf_model.type = RbfType.THINPLATE
        r_thinplate = np.array([1.0, 2.0, 3.0])
        result_thinplate = self.rbf_model.phi(r_thinplate)
        expected_thinplate = np.array([0.0, 2.77258872, 9.8875106])
        np.testing.assert_allclose(
            np.array(result_thinplate), expected_thinplate
        )
        assert self.rbf_model.phi(4.0) == (
            4 * 4 * np.log(4 + sys.float_info.min)
        )

        # self.rbf_model.type = RbfType(-1)
        # r_invalid_type = np.array([1.0, 2.0, 3.0])
        # try:
        #     self.rbf_model.phi(r_invalid_type)
        # except ValueError as e:
        #     assert str(e) == "Unknown RbfType"
        # else:
        #     assert False, "Expected ValueError not raised"

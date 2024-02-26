"""Sampling strategies for the optimization algorithms.
"""

# Copyright (C) 2024 National Renewable Energy Laboratory
# Copyright (C) 2014 Cornell University

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

__authors__ = [
    "Juliane Mueller",
    "Christine A. Shoemaker",
    "Haoyu Jia",
    "Weslley S. Pereira",
]
__contact__ = "juliane.mueller@nrel.gov"
__maintainer__ = "Weslley S. Pereira"
__email__ = "weslley.dasilvapereira@nrel.gov"
__credits__ = [
    "Juliane Mueller",
    "Christine A. Shoemaker",
    "Haoyu Jia",
    "Weslley S. Pereira",
]
__version__ = "0.1.0"
__deprecated__ = False

from enum import Enum
import numpy as np


class SamplingStrategy(Enum):
    NORMAL = 1  # normal distribution
    DDS = 2  # DDS. Used in the DYCORS algorithm
    UNIFORM = 3  # uniform distribution
    DDS_UNIFORM = 4  # sample twice, first DDS then uniform distribution if there is no fixed variable


class Sampler:
    """Base class for samplers.

    Attributes
    ----------
    strategy : SamplingStrategy
        Sampling strategy.
    n : int
        Number of samples to be generated.
    """

    def __init__(self, n: int) -> None:
        self.strategy = SamplingStrategy.UNIFORM
        self.n = n
        assert self.n > 0

    def get_uniform_sample(
        self, bounds: tuple | list, *, iindex: tuple = ()
    ) -> np.ndarray:
        """Generate a sample from a uniform distribution inside the bounds.

        Parameters
        ----------
        bounds : tuple | list
            Bounds for variables. Each element of the tuple must be a tuple with two elements,
            corresponding to the lower and upper bound for the variable.
        iindex : tuple, optional
            Indices of the input space that are integer. The default is ().

        Returns
        -------
        numpy.ndarray
            Matrix with the generated samples.
        """
        dim = len(bounds)
        xlow = np.array([bounds[i][0] for i in range(dim)])
        xup = np.array([bounds[i][1] for i in range(dim)])

        # Generate n samples
        xnew = xlow + np.random.rand(self.n, dim) * (xup - xlow)

        # Round integer variables
        xnew[:, iindex] = np.round(xnew[:, iindex])

        return xnew

    get_sample = get_uniform_sample


class NormalSampler(Sampler):
    """Sampler that generates samples from a normal distribution.

    Attributes
    ----------
    sigma : float
        Standard deviation of the normal distribution, relative to the minimum
        range of the input space.
    sigma_min : float
        Minimum standard deviation of the normal distribution, relative to the
        minimum range of the input space.
    sigma_max : float
        Maximum standard deviation of the normal distribution, relative to the
        minimum range of the input space.
    """

    def __init__(
        self,
        n: int,
        sigma: float,
        *,
        sigma_min: float = 0,
        sigma_max: float = float("inf"),
        strategy: SamplingStrategy = SamplingStrategy.NORMAL,
    ) -> None:
        super().__init__(n)
        self.sigma = sigma
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.strategy = strategy
        assert (
            0 <= self.sigma_min <= self.sigma <= self.sigma_max <= float("inf")
        )
        assert self.strategy in (
            SamplingStrategy.NORMAL,
            SamplingStrategy.DDS,
            SamplingStrategy.UNIFORM,
            SamplingStrategy.DDS_UNIFORM,
        )

    def get_normal_sample(
        self,
        bounds: tuple | list,
        *,
        iindex: tuple = (),
        mu: np.ndarray = np.array([0]),
        coord=(),
    ) -> np.ndarray:
        """Generate a sample from a normal distribution around a given point mu.

        Parameters
        ----------
        bounds : tuple | list
            Bounds for variables. Each element of the tuple must be a tuple with two elements,
            corresponding to the lower and upper bound for the variable.
        iindex : tuple, optional
            Indices of the input space that are integer. The default is ().
        mu : numpy.ndarray, optional
            Point around which the sample will be generated. The default is zero.
        coord : tuple, optional
            Coordinates of the input space that will vary. The default is (), which means that all
            coordinates will vary.

        Returns
        -------
        numpy.ndarray
            Matrix with the generated samples.
        """
        dim = len(bounds)
        xlow = np.array([bounds[i][0] for i in range(dim)])
        xup = np.array([bounds[i][1] for i in range(dim)])

        mixrange = (xup - xlow).min()
        sigma = self.sigma * mixrange

        # Check if mu is valid
        xnew = np.tile(mu, (self.n, 1))
        if xnew.shape != (self.n, dim):
            raise ValueError(
                "mu must either be a scalar or a vector of size dim"
            )

        # Generate n samples
        if len(coord) == 0:
            coord = tuple(range(dim))
        xnew[:, coord] += sigma * np.random.randn(self.n, len(coord))
        xnew[:, coord] = np.maximum(xlow, np.minimum(xnew[:, coord], xup))

        # Round integer variables
        xnew[:, iindex] = np.round(xnew[:, iindex])

        return xnew

    def get_dds_sample(
        self,
        bounds: tuple | list,
        probability: float,
        *,
        iindex: tuple = (),
        mu: np.ndarray = np.array([0]),
        coord=(),
    ) -> np.ndarray:
        """Generate a DDS sample.

        Parameters
        ----------
        bounds : tuple | list
            Bounds for variables. Each element of the tuple must be a tuple with two elements,
            corresponding to the lower and upper bound for the variable.
        probability : float
            Perturbation probability.
        iindex : tuple, optional
            Indices of the input space that are integer. The default is ().
        mu : numpy.ndarray, optional
            Point around which the sample will be generated. The default is zero.
        coord : tuple, optional
            Coordinates of the input space that will vary. The default is (), which means that all
            coordinates will vary.

        Returns
        -------
        numpy.ndarray
            Matrix with the generated samples.
        """
        dim = len(bounds)
        xlow = np.array([bounds[i][0] for i in range(dim)])
        xup = np.array([bounds[i][1] for i in range(dim)])

        mixrange = (xup - xlow).min()
        sigma = self.sigma * mixrange

        # Check if mu is valid
        xnew = np.tile(mu, (self.n, 1))
        if xnew.shape != (self.n, dim):
            raise ValueError(
                "mu must either be a scalar or a vector of size dim"
            )

        # Check if probability is valid
        if not (0 <= probability <= 1):
            raise ValueError("Probability must be between 0 and 1")

        # generate n samples
        if len(coord) == 0:
            coord = tuple(range(dim))
        cdim = len(coord)
        for ii in range(self.n):
            r = np.random.rand(cdim)
            ar = r < probability
            if not (any(ar)):
                r = np.random.permutation(cdim)
                ar[r[0]] = True
            for jj in range(cdim):
                if ar[jj]:
                    s_std = sigma * np.random.randn(1).item()
                    j = coord[jj]
                    if j in iindex:
                        # integer perturbation has to be at least 1 unit
                        if abs(s_std) < 1:
                            s_std = np.sign(s_std)
                        else:
                            s_std = np.round(s_std)
                    xnew[ii, j] = xnew[ii, j] + s_std

                    if xnew[ii, j] < xlow[j]:
                        xnew[ii, j] = xlow[j] + (xlow[j] - xnew[ii, j])
                        if xnew[ii, j] > xup[j]:
                            xnew[ii, j] = xlow[j]
                    elif xnew[ii, j] > xup[j]:
                        xnew[ii, j] = xup[j] - (xnew[ii, j] - xup[j])
                        if xnew[ii, j] < xlow[j]:
                            xnew[ii, j] = xup[j]
        return xnew

    def get_sample(
        self,
        bounds: tuple | list,
        *,
        iindex: tuple = (),
        mu: np.ndarray = np.array([0]),
        probability: float = 1,
        coord=(),
    ) -> np.ndarray:
        """Generate a sample.

        Parameters
        ----------
        bounds : tuple | list
            Bounds for variables. Each element of the tuple must be a tuple with two elements,
            corresponding to the lower and upper bound for the variable.
        iindex : tuple, optional
            Indices of the input space that are integer. The default is ().
        mu : numpy.ndarray, optional
            Point around which the sample will be generated. The default is zero.
        probability : float, optional
            Perturbation probability. The default is 1.
        coord : tuple, optional
            Coordinates of the input space that will vary. The default is (),
            which means that all coordinates will vary.

        Returns
        -------
        numpy.ndarray
            Matrix with the generated samples.
        """
        if self.strategy == SamplingStrategy.UNIFORM:
            assert coord == ()
            return self.get_uniform_sample(bounds, iindex=iindex)
        elif self.strategy == SamplingStrategy.NORMAL:
            return self.get_normal_sample(
                bounds, iindex=iindex, mu=mu, coord=coord
            )
        elif self.strategy == SamplingStrategy.DDS:
            return self.get_dds_sample(
                bounds, probability, iindex=iindex, mu=mu, coord=coord
            )
        elif self.strategy == SamplingStrategy.DDS_UNIFORM:
            if len(coord) > 0:
                return self.get_dds_sample(
                    bounds, probability, iindex=iindex, mu=mu, coord=coord
                )
            else:
                return np.concatenate(
                    (
                        self.get_dds_sample(
                            bounds,
                            probability,
                            iindex=iindex,
                            mu=mu,
                        ),
                        self.get_uniform_sample(bounds, iindex=iindex),
                    ),
                    axis=0,
                )
        else:
            raise ValueError("Invalid sampling strategy")

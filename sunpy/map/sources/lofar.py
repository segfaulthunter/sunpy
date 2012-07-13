import h5py
import numpy as np

from matplotlib import pyplot as plt

class LOFARSpectrogram(h5py._hl.dataset.Dataset):
	""" This is *NOT* a numpy array as that would be too large to hold
	in memory. """
	def __init__(self, id_, x_range=None, y_range=None):
		h5py._hl.dataset.Dataset.__init__(self, id_)
		if x_range is None:
			x_range = (0, self.shape[0])

		if y_range is None:
			y_range = (0, self.shape[1])

		self.x_range = x_range
		self.y_range = y_range

		self.xsize = self.x_range[1] - self.x_range[0]
		self.ysize = self.y_range[1] - self.y_range[0]

	def subsample_to(self, cols, rows):
		# cols and rows are swapped because the result is transposed.
		return self[self.x_range[0]:self.x_range[1]:self.xsize // cols,
					self.y_range[0]:self.y_range[1]:self.ysize // rows].T

	def slice(self, start, end): # XXX: Remove
		return self.__class__(self._id, (start, end))

	@classmethod
	def read(cls, filepath):
		fle = h5py.File(filepath)
		# XXX: Implement
		return cls(fle["SUB_ARRAY_POINTING_000/BEAM_000/STOKES_0"].id)


if __name__ == '__main__':
	lofar = LOFARSpectrogram.read("L60935_SAP000_B000_S0_P000_bf.h5")
	plt.imshow(lofar.slice(45000, 50000).subsample_to(800, 600))
	plt.show()
	raw_input()
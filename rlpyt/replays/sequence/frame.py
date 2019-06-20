import numpy as np

from rlpyt.replays.sequence.n_step import SequenceNStepReturnBuffer
from rlpyt.replays.frame import FrameBufferMixin
from rlpyt.replays.sequence.uniform import UniformSequenceReplay
from rlpyt.replays.sequence.prioritized import PrioritizedSequenceReplay


class SequenceNStepFrameBuffer(FrameBufferMixin, SequenceNStepReturnBuffer):

    def extract_observation(self, T_idxs, B_idxs, T):
        """Frames are returned OLDEST to NEWEST."""
        observation = np.empty(shape=(T, len(B_idxs), self.n_frames) +  # [T,B,C,H,W]
            self.samples_frames.shape[2:], dtype=self.samples_frames.dtype)
        fm1 = self.n_frames - 1
        for i, (t, b) in enumerate(zip(T_idxs, B_idxs)):
            if t + T >= self.T:  # wrap (n_frames duplicated)
                m = self.T - t
                w = T - m
                for f in range(self.n_frames):
                    observation[:m, i, f] = self.samples_frames[t + f:t + f + m, b]
                    observation[m:, i, f] = self.samples_frames[f:w + f, b]
                    if self.samples.done[t - f, b]:
                        observation[0, i, f - 1:-1] = 0
            else:
                for f in range(self.n_frames):
                    observation[:, i, f] = self.samples_frames[t + f:t + f + T, b]

            # Populate empty (zero) frames after environment done.
            if t - fm1 < 0 or t + T > T:  # Wrap.
                done_idxs = np.arange(t - fm1, t + T) % self.T
            else:
                done_idxs = slice(t - fm1, t + T)
            done_fm1 = self.samples.done[done_idxs, b]
            if np.any(done_fm1):
                where_done_t = np.where(done_fm1)[0] - fm1  # Might be negative...
                for f in range(1, self.n_frames):
                    t_blanks = where_done_t + f  # ...might be > T...
                    t_blanks = t_blanks[t_blanks >= 0 and t_blanks < T]  # ..don't let it wrap.
                    observation[t_blanks, i, :self.n_frames - f] = 0

        return observation


class UniformSequenceReplayFrameBuffer(UniformSequenceReplay,
        SequenceNStepFrameBuffer):

    pass


class PrioritizedSequenceReplayFrameBuffer(PrioritizedSequenceReplay,
        SequenceNStepFrameBuffer):

    pass

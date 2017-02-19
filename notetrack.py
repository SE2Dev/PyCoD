class NoteTrack:
	def __init__(self, frame, string=""):
		self.frame = frame
		self.string = string

class NoteTrack_Export:
	def __init__(self, path=None):
		if(path is None):
			self.notes = []
			self.frame_count = None
		else:
			self.LoadFile(path)

	def LoadFile(self, path):
		self.notes = []
		self.first_frame = None
		self.frame_count = None
		file = open(path, "r")
		for line in file:
			line = line.lstrip()
			if line.startswith("//"):
				continue

			note_count = 0

			line_split = line.split()
			if line_split[0] == "FIRSTFRAME":
				self.first_frame = int(line_split[1])
			elif line_split[0] == "NUMFRAMES":
				self.frame_count = int(line_split[1])
			elif line_split[0] == "NUMKEYS":
				note_count = int(line_split[1])
			elif line_split[0] == "FRAME":
				note = NoteTrack(int(line_split[1]), line_split[2][1:-1])
				self.notes.append(note)
		file.close()	

	def WriteFile(self, path):
		file = open(path, "w")
		file.write("FIRSTFRAME %d\n" % self.first_frame)
		file.write("NUMFRAMES %d\n" % self.frame_count)
		file.write("NUMKEYS %d\n" % len(self.notes))
		for note in self.notes:
			file.write("FRAME %d \"%s\"\n" % (note.frame, note.string))
		file.close()

	"""
	The following are just accessors for various properties of the notetrack file
	"""
	# Literally the first keyed frame in the XANIM_EXPORT file
	def FirstFrame(self):
		return self.first_frame

	# The number of frames in the XANIM_EXPORT file
	def NumFrames(self):
		return self.frame_count

	# The number of notes in this (the NT_EXPORT) file
	def NumKeys(self):
		return len(self.notes)

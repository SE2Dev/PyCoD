from itertools import islice
from time import strftime
from os.path import dirname, basename, splitext

# NT_EXPORT

class Note(object):
	__slots__=('frame', 'string')
	def __init__(self, frame, string=""):
		self.frame = frame
		self.string = string

class NoteTrack(object):
	__slots__=('notes', 'frame_count', 'first_frame')
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
			note_count = 0

			line_split = line.split()
			if line_split[0] == "FIRSTFRAME":
				self.first_frame = int(line_split[1])
			elif line_split[0] == "NUMFRAMES":
				self.frame_count = int(line_split[1])
			elif line_split[0] == "NUMKEYS":
				note_count = int(line_split[1])
			elif line_split[0] == "FRAME":
				note = Note(int(line_split[1]), line_split[2][1:-1])
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

# XANIM_EXPORT

def __clamp_float__(value, range=(-1.0, 1.0)):
	return max(min(value, range[1]), range[0])

def __clamp_multi__(value, range=(-1.0, 1.0)):
	return tuple([max(min(v, range[1]), range[0]) for v in value])

# In the context of an XANIM_EXPORT file, a 'part' is essentially a bone
class PartInfo:
	def __init__(self, name):
		self.name = name

class FramePart:
	def __init__(self, offset=None):
		if offset is None:
			self.offset = None
		else:
			self.offset = offset
		self.matrix = [(),(),()]

class Frame:
	def __init__(self, frame):
		self.frame = frame

	def __load_part__(self, file, part_count):
		lines_read = 0

		# keeps track of the importer state for a given part
		state = 0

		part_index = -1
		part = None

		for line in file:
			lines_read += 1

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if state == 0 and line_split[0] == "PART":
				part_index = int(line_split[1])
				if(part_index >= part_count):
					raise ValueError("part_count does not index part_index -- %d not in [0, %d)" % (part_index, part_count))
				state = 1
			elif state == 1 and line_split[0] == "OFFSET":
				offset = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				self.parts[part_index] = FramePart(offset)
				part = self.parts[part_index]
				state = 2
			elif state == 2 and line_split[0] == "X":
				x = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				part.matrix[0] = x
				state = 3
			elif state == 3 and line_split[0] == "Y":
				y = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				part.matrix[1] = y
				state = 4
			elif state == 4 and line_split[0] == "Z":
				z = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				part.matrix[2] = z
				state = -1
				return lines_read

		return lines_read

	def _load_parts_(self, file, part_count):
		self.parts = [FramePart()] * part_count

		lines_read = 0
		for part in range(part_count):
			lines_read += self.__load_part__(file, part_count)
		return lines_read

class XAnim_Export:
	def __init__(self, path=None):
		if(path is None):
			self.parts = []
		else:
			self.LoadFile(path)

	
	def __load_header__(self, file):
		lines_read = 0
		is_anim = False
		for line in file:
			lines_read += 1

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "ANIMATION":
				is_anim = True
			elif is_anim == True and line_split[0] == "VERSION":
				self.version = int(line_split[1])
				return lines_read

		return lines_read

	def __load_part_info__(self, file):
		lines_read = 0
		part_count = 0
		parts_read = 0
		for line in file:
			lines_read += 1

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "NUMPARTS":
				part_count = int(line_split[1])
				self.parts = [PartInfo(None)] * part_count
			elif line_split[0] == "PART":
				index = int(line_split[1])
				self.parts[index] = PartInfo(line_split[2][1:-1])
				parts_read += 1
				if parts_read == part_count:
					return lines_read

		return lines_read

	def __load_frames__(self, file):
		lines_read = 0
		frame_count = 0
		frame_index = 0
		self.frames = [Frame(-1)] * 0
		for line in file:
			lines_read += 1

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "FRAMERATE":
				# TODO: Check if the format even supports non-int framerates
				self.framerate = float(line_split[1])
			elif line_split[0] == "NUMFRAMES":
				frame_count = int(line_split[1])
				self.frames = [None]*frame_count
			elif line_split[0] == "FRAME":
				# TODO: Check if the format supports non-int frames
				frame_number = int(line_split[1])

				#  Don't enable this until anims that don't start on frame 0 are sorted out
				#if frame_number >= frame_count:
				#	raise ValueError("frame_count does not index frame_number -- %d not in [0, %d)" % (frame_number, frame_count))
				
				lines_read += self.__load_frame__(file, frame_index, frame_number)
				frame_index += 1

				if frame_index == frame_count:
					return lines_read
		
		return lines_read

	def __load_frame__(self, file, frame_index, frame_number):
		frame = Frame(frame_number)
		lines_read = frame._load_parts_(file, len(self.parts))
		self.frames[frame_index] = frame
		return lines_read

	def __load_notes__(self, file):
		lines_read = 0
		note_count = 0
		note_index = 0
		self.notes = [Note(-1)] * 0
		state = 0
		for line in file:
			lines_read += 1

			line_split = line.split()
			if len(line_split) == 0:
				continue

			# Skipping the extraneous data seems to be the fastest way to load these
			# All relevent notes follow a numkeys label
			if state == 0 and line_split[0] == "NUMKEYS":
				note_count = int(line_split[1])

				# Start looking for frames if there are actually any keys
				if note_count != 0:
					state = 1
			elif state == 1 and line_split[0] == "FRAME":
				frame = int(line_split[1])
				string = line_split[2][1:-1]
				note = Note(frame, string)
				self.notes.append(note)

				if note_index == note_count:
					note_index = 0
					note_count = 0
					state = 0
					
			"""
			TODO: Add notetrack read support - implicitly handle both WAW and BO1 styles
				The embedded notetrack format appears to be somewhat inconsistent between WaW and BO1
				This needs to be addressed
			"""
		return lines_read

	def LoadFile(self, path):
		file = open(path, "r")
		# file automatically keeps track of what line its on across calls
		self.__load_header__(file)
		self.__load_part_info__(file)
		self.__load_frames__(file)
		self.__load_notes__(file)
		file.close()

	# Write an XANIM_EXPORT file
	# if embed_notes is False, a NT_EXPORT file will be created
	def WriteFile(self, path, header_message="", embed_notes=True):
		first_frame = 0
		last_frame = 0
		if len(self.frames) != 0:
			first_frame = min([frame.frame for frame in self.frames])
			last_frame = max([frame.frame for frame in self.frames]) + 1

		if last_frame - first_frame != len(self.frames):
			raise ValueError("The keyed frame count and number of frames do not match")

		file = open(path, "w")
		file.write(header_message)
		file.write("// Export time: %s\n\n" % strftime("%a %b %d %H:%M:%S %Y"))

		file.write("ANIMATION\n")
		file.write("VERSION %d\n\n" % self.version)
	
		file.write("NUMPARTS %d\n" % len(self.parts))
		for part_index, part in enumerate(self.parts):
			file.write("PART %d \"%s\"\n" % (part_index, part.name))
		file.write("\n")

		file.write("FRAMERATE %d\n" % self.framerate)
		file.write("NUMFRAMES %d\n" % len(self.frames))
		for frame in self.frames:
			file.write("FRAME %d\n" % frame.frame)
			for part_index, part in enumerate(frame.parts):
				file.write("PART %d\n" % part_index)
				# TODO: Investigate precision options
				file.write("OFFSET %f %f %f\n" % (part.offset[0], part.offset[1], part.offset[2]))
				file.write("X %f %f %f\n" % __clamp_multi__(part.matrix[0]))
				file.write("Y %f %f %f\n" % __clamp_multi__(part.matrix[1]))
				file.write("Z %f %f %f\n\n" % __clamp_multi__(part.matrix[2]))

		# NOTE: Despite having the same version number, BO1 supports the NUMKEYS style embedded notetracks
		#  While WAW doesn't, so in order to support both we'll use the WAW way since both games support it
		# TODO: Verify how notetracks work across versions (Specifically for CoD2)
		# TODO: Support for NT_EXPORT file generation - and automatically formatting the XANIM_EXPORT to correspond to this

		# WAW Style
		file.write("NOTETRACKS\n\n")
		if embed_notes == True:
			for part_index, part in enumerate(self.parts):
				file.write("PART %d\n" % part_index)
				track_count = 0 if part_index != 0 else (1 if len(self.notes) != 0 else 0)
				file.write("NUMTRACKS %d\n\n" % track_count)
				if track_count != 0:
					file.write("NOTETRACK 0\n")
					file.write("NUMKEYS %d\n" % len(self.notes))
					for note in self.notes:
						file.write("FRAME %d \"%s\"\n" % (note.frame, note.string))
					file.write("\n")
		
		# Write a NT_EXPORT file
		else:
			notetrack = NoteTrack()
			notetrack.notes = self.notes
			notetrack.first_frame = first_frame
			notetrack.frame_count = last_frame - first_frame
			
			_dir = dirname(path)
			_file = splitext(basename(path))[0]

			notetrack.WriteFile("%s/%s.NT_EXPORT" % (_dir, _file))

		# BO1 Style (Just here for reference)
		#file.write("NUMKEYS %d\n" % len(self.notes))
		#	for note in self.notes:
		#		file.write("FRAME %d \"%s\"\n" % (note.frame, note.string))
		#	file.write("\n")

		file.close()

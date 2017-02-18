from itertools import islice
from notetrack import NoteTrack

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
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

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
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "ANIMATION":
				is_anim = True
			elif is_anim == True:
				self.version = int(line_split[1])
				return lines_read

		return lines_read

	def __load_part_info__(self, file):
		lines_read = 0
		part_count = 0
		parts_read = 0
		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

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
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "FRAMERATE":
				# TODO: Check if the format even supports non-int point framerates
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
		
		return lines_read

	def __load_frame__(self, file, frame_index, frame_number):
		frame = Frame(frame_number)
		lines_read = frame._load_parts_(file, len(self.parts))
		self.frames[frame_index] = frame
		return lines_read

	def __load_notes__(self, file):
		lines_read = 0
		self.notes = []
		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "NOTETRACKS":
				continue
			
			"""
			TODO: Add notetrack read support
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

	def WriteFile(self, path):
		file = open(path, "w")
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
				file.write("X %f %f %f\n" % (part.matrix[0][0], part.matrix[0][1], part.matrix[0][2]))
				file.write("Y %f %f %f\n" % (part.matrix[1][0], part.matrix[1][1], part.matrix[1][2]))
				file.write("Z %f %f %f\n\n" % (part.matrix[2][0], part.matrix[2][1], part.matrix[2][2]))

		# TODO: Verify how notetracks work across versions
		if len(self.notes) > 0:
			raise ValueError("len(notes) > 0 - notes aren't currently supported")
		file.write("NUMKEYS %d\n" % len(self.notes))

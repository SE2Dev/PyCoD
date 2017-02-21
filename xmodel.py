from itertools import islice, repeat
from notetrack import NoteTrack
from time import strftime

class Bone:
	def __init__(self, name, parent=None):
		self.name = name
		self.parent = parent
		self.offset = None
		self.matrix = [None] * 3

class Material:
	def __init__(self, name, type, image):
		self.name = name
		self.type = type
		self.image = image
		self.color = None
		self.color_ambient = None
		self.color_specular = None
		self.color_reflective = None
		self.transparency = None
		self.incandescence = None
		self.coeffs = None
		self.glow = None
		self.refractive = None
		self.reflective = None
		self.blinn = None
		self.phong = None

class XModel_Export:
	def __init__(self, path=None):
		if(path is None):
			self.bones = []
			self.verts = []
			self.indices = []
			self.normals = []
			self.colors = []
			self.uvs = []

			self.bone_groups = []
			self.mesh_groups = []
			self.material_groups = []
		else:
			self.LoadFile(path)

	def __load_header__(self, file):
		lines_read = 0
		state = 0
		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if state == 0 and line_split[0] == "MODEL":
				state = 1
			elif state == 1 and line_split[0] == "VERSION":
				self.version = int(line_split[1])
				return lines_read

		return lines_read

	def __load_bones__(self, file):
		lines_read = 0
		bone_count = 0
		bones_read = 0
		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "NUMBONES":
				bone_count = int(line_split[1])
				self.bones = [Bone(None)] * bone_count
			elif line_split[0] == "BONE":
				index = int(line_split[1])
				parent = int(line_split[2])
				self.bones[index] = Bone(line_split[3][1:-1], parent)
				bones_read += 1
				if bones_read == bone_count:
					break

		for bone in range(bone_count):
			lines_read += self.__load_bone__(file, bone_count)

		return lines_read

	def __load_bone__(self, file, bone_count):
		lines_read = 0

		# keeps track of the importer state for a given bone
		state = 0

		bone_index = -1
		bone = None

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if state == 0 and line_split[0] == "BONE":
				bone_index = int(line_split[1])
				if(bone_index >= bone_count):
					raise ValueError("bone_count does not index bone_index -- %d not in [0, %d)" % (bone_index, bone_count))
				state = 1
			elif state == 1 and line_split[0] == "OFFSET":
				bone = self.bones[bone_index]
				bone.offset = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				state = 2
			# SCALE ... is ignored as its always 1
			elif state == 2 and line_split[0] == "X":
				x = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				bone.matrix[0] = x
				state = 3
			elif state == 3 and line_split[0] == "Y":
				y = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				bone.matrix[1] = y
				state = 4
			elif state == 4 and line_split[0] == "Z":
				z = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				bone.matrix[2] = z
				state = -1
				return lines_read

		return lines_read

	def __load_vert__(self, file, vert_count):
		lines_read = 0
		state = 0

		vert_index = -1
		vert = None

		bone_count = 0 # The number of bones influencing this vertex
		bones_read = 0 # The number of bone weights we've read for this vert

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if state == 0 and line_split[0] == "VERT":
				vert_index = int(line_split[1])
				if(vert_index >= vert_count):
					raise ValueError("vert_count does not index vert_index -- %d not in [0, %d)" % (vert_index, vert_count))
				state = 1
			elif state == 1 and line_split[0] == "OFFSET":
				self.verts[vert_index] = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				state = 2
			elif state == 2 and line_split[0] == "BONES":
				bone_count = int(line_split[1])
				state = 3
			elif state == 3 and line_split[0] == "BONE":
				bone = int(line_split[1])
				influence = float(line_split[2])

				self.bone_groups[bone].append((vert_index, influence))
				bones_read += 1
				if bones_read == bone_count:
					state = -1
					return lines_read
		
		return lines_read

	def __load_verts__(self, file):
		lines_read = 0
		vert_count = 0

		self.bone_groups = [[] for i in repeat(None, len(self.bones))]

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "NUMVERTS":
				vert_count = int(line_split[1])
				self.verts = [None] * vert_count
				self.weights = [None] * vert_count
				break

		for vertex in range(vert_count):
			lines_read += self.__load_vert__(file, vert_count)

		return lines_read

	def __load_face__(self, file, face_count):
		lines_read = 0
		state = 0

		face = None

		vert_number = -1
		indices = [None] * 3
		normals = [None] * 3
		colors = [None] * 3
		uvs = [None] * 3

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if state == 0 and line_split[0] == "TRI":
				mesh_index = int(line_split[1])
				extend_size = (mesh_index + 1) - len(self.mesh_groups)
				if extend_size > 0:
					self.mesh_groups.extend([[] for i in repeat(None, extend_size)])
					
				material_index = int(line_split[2])
				extend_size = (material_index + 1) - len(self.material_groups)
				if extend_size > 0:
					self.material_groups.extend([[] for i in repeat(None, extend_size)])
				state = 1
			elif state == 1 and line_split[0] == "VERT":
				indices[vert_number] = int(line_split[1])
				vert_number += 1
				state = 2
			elif state == 2 and line_split[0] == "NORMAL":
				normals[vert_number] = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				state = 3
			elif state == 3 and line_split[0] == "COLOR":
				colors[vert_number] = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
				state = 4
			elif state == 4 and line_split[0] == "UV":
				uvs = (float(line_split[1]), float(line_split[2]))
				if vert_number == 2:
					self.indices.append(indices)
					self.normals.append(normals)
					self.colors.append(colors)
					self.uvs.append(uvs)
					self.material_groups[material_index].extend(indices)
					self.mesh_groups[mesh_index].extend(indices)
					return lines_read
				else:
					state = 1
		
		return lines_read

	def __load_faces__(self, file):
		lines_read = 0
		face_count = 0

		self.indices = []
		self.normals = []
		self.colors = []
		self.uvs = []

		self.mesh_groups = []
		self.material_groups = []

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if line_split[0] == "NUMFACES":
				face_count = int(line_split[1])
				break
		
		for face in range(face_count):
			lines_read += self.__load_face__(file, face_count)

		return lines_read

	def __load_meshes__(self, file):
		lines_read = 0
		mesh_count = 0
		meshes_read = 0
		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			if line_split[0] == "NUMOBJECTS":
				mesh_count = int(line_split[1])
				self.meshes = [None] * mesh_count
			elif line_split[0] == "OBJECT":
				index = int(line_split[1])
				self.meshes[index] = line_split[2][1:-1]
				meshes_read += 1
				if meshes_read == mesh_count:
					return lines_read

		return lines_read

	def __load_materials__(self, file):
		lines_read = 0

		material_count = None
		material = None

		for line in file:
			lines_read += 1
			line = line.lstrip()
			if line.startswith("//"):
				continue

			line_split = line.split()
			if len(line_split) == 0:
				continue

			for i, split in enumerate(line_split):
				if split[-1:] == ',':
					line_split[i] = split.rstrip(",")

			if material_count == None and line_split[0] == "NUMMATERIALS":
				material_count = int(line_split[1])
				self.materials = [None] * material_count
			elif line_split[0] == "MATERIAL":
				index = int(line_split[1])
				name = line_split[2][1:-1]
				type = line_split[3][1:-1]
				image = line_split[4][1:-1]
				material = Material(name, type, image)
				self.materials[index] = Material(name, type, image)
				material = self.materials[index] 
			elif line_split[0] == "COLOR":
				material.color = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "TRANSPARENCY":
				material.transparency = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "AMBIENTCOLOR":
				material.color_ambient = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "INCANDESCENCE":
				material.incandescence = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "COEFFS":
				material.coeffs = (float(line_split[1]), float(line_split[2]))
			elif line_split[0] == "GLOW":
				material.glow = (float(line_split[1]), int(line_split[2]))
			elif line_split[0] == "REFRACTIVE":
				material.refractive = (int(line_split[1]), float(line_split[2]))
			elif line_split[0] == "SPECULARCOLOR":
				material.color_specular = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "REFLECTIVECOLOR":
				material.color_reflective = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
			elif line_split[0] == "REFLECTIVE":
				material.reflective = (int(line_split[1]), float(line_split[2]))
			elif line_split[0] == "BLINN":
				material.blinn = (float(line_split[1]), float(line_split[2]))
			elif line_split[0] == "PHONG":
				material.phong = float(line_split[1])
		
		return lines_read

	def LoadFile(self, path):
		file = open(path, "r")
		# file automatically keeps track of what line its on across calls
		self.__load_header__(file)
		self.__load_bones__(file)
		
		self.__load_verts__(file)
		self.__load_faces__(file)
		
		self.__load_meshes__(file)
		self.__load_materials__(file)

		for group_index, group in enumerate(self.bone_groups):
			self.bone_groups[group_index] = list(set(group))

		for group_index, group in enumerate(self.mesh_groups):
			self.mesh_groups[group_index] = list(set(group))

		for group_index, group in enumerate(self.material_groups):
			self.material_groups[group_index] = list(set(group))

		file.close()

	def WriteFile(self, path):
		# TODO: WriteFile()
		return

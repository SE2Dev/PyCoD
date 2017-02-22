from itertools import repeat
from time import strftime

class Bone(object):
	__slots__ = ('name', 'parent', 'offset', 'matrix')
	def __init__(self, name, parent=-1):
		self.name = name
		self.parent = parent
		self.offset = None
		self.matrix = [None] * 3

class Vertex(object):
	__slots__ = ("offset", "weights")
	def __init__(self):
		self.offset = None
		self.weights = [] # An array of tuples in the format (bone index, influence)

	def __load_vert__(self, file, vert_count, mesh):
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
				self.offset = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				state = 2
			elif state == 2 and line_split[0] == "BONES":
				bone_count = int(line_split[1])
				self.weights = [None] * bone_count
				state = 3
			elif state == 3 and line_split[0] == "BONE":
				bone = int(line_split[1])
				influence = float(line_split[2])
				self.weights[bones_read] = ((bone, influence))
				bones_read += 1
				if bones_read == bone_count:
					state = -1
					return lines_read
		
		return lines_read

	def save(self, file, index):
		file.write("VERT %d\n" % index)
		file.write("OFFSET %f %f %f\n" % self.offset)
		file.write("BONES %d\n" % len(self.weights))
		for weight in self.weights:
			file.write("BONE %d %f\n" % weight)
		file.write("\n")

class FaceVertex(object):
	__slots__ = ("vertex", "normal", "color", "uv")
	def __init__(self, vertex=None, normal=None, color=None, uv=None):
		self.vertex = vertex
		self.normal = normal
		self.color = color
		self.uv = uv

	def save(self, file, index_offset):
		file.write("VERT %d\n" % (self.vertex + index_offset))
		file.write("NORMAL %f %f %f\n" % self.normal)
		file.write("COLOR %f %f %f %f\n" % self.color)
		file.write("UV 1 %f %f\n\n" % self.uv)

class Face(object):
	__slots__ = ('mesh_id', 'material_id', 'indices')
	def __init__(self, mesh_id, material_id):
		self.mesh_id = mesh_id
		self.material_id = material_id
		self.indices = [None] * 3

	def __load_face__(self, file, face_count):
		lines_read = 0
		state = 0

		face = None

		tri_number = -1
		vert_number = -1

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
				tri_number += 1
				self.mesh_id = int(line_split[1])	
				self.material_id = int(line_split[2])
				state = 1
			elif state == 1 and line_split[0] == "VERT":
				vert = FaceVertex()
				vert.vertex = int(line_split[1])
				vert_number += 1
				state = 2
			elif state == 2 and line_split[0] == "NORMAL":
				vert.normal = (float(line_split[1]), float(line_split[2]), float(line_split[3]))
				state = 3
			elif state == 3 and line_split[0] == "COLOR":
				vert.color = (float(line_split[1]), float(line_split[2]), float(line_split[3]), float(line_split[4]))
				state = 4
			elif state == 4 and line_split[0] == "UV":
				vert.uv = (float(line_split[2]), float(line_split[3]))
				self.indices[vert_number] = vert
				if vert_number == 2:
					return lines_read
				else:
					state = 1
		
		return lines_read

	def save(self, file, index_offset):
		file.write("TRI %d %d %d %d\n" % (self.mesh_id, self.material_id, 0, 0))
		for i in range(3):
			self.indices[i].save(file, index_offset)
		file.write("\n")

class Material:
	__slots__ = (
					'name', 'type', 'image',
				 	'color', 'color_ambient', 'color_specular', 'color_reflective',
				 	'transparency', 'incandescence', 
				 	'coeffs', 'glow',
				 	'refractive', 'reflective',
				 	'blinn', 'phong'
				)
	def __init__(self, name, material_type, image):
		self.name = name
		self.type = material_type
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

	def save(self, file, material_index):
		file.write('MATERIAL %d "%s" "%s" "%s"\n' % (material_index, self.name, self.type, self.image))
		file.write("COLOR %f %f %f %f\n" % self.color)
		file.write("TRANSPARENCY %f %f %f %f\n" % self.transparency)
		file.write("AMBIENTCOLOR %f %f %f %f\n" % self.color_ambient)
		file.write("INCANDESCENCE %f %f %f %f\n" % self.incandescence)
		file.write("COEFFS %f %f\n" % self.coeffs)
		file.write("GLOW %f %d\n" % self.glow)
		file.write("REFRACTIVE %d %f\n" % self.refractive)
		file.write("SPECULARCOLOR %f %f %f %f\n" % self.color_specular)
		file.write("REFLECTIVECOLOR %f %f %f %f\n" % self.color_reflective)
		file.write("REFLECTIVE %d %f\n" % self.reflective)
		file.write("BLINN %f %f\n" % self.blinn)
		file.write("PHONG %f\n\n" % self.phong)

class Mesh(object):
	__slots__ = ('name', 'verts', 'faces', 'bone_groups', 'material_groups')
	def __init__(self, name):
		self.name = name

		self.verts = []
		self.faces = []

		self.bone_groups = []
		self.material_groups = []

	def __load_verts__(self, file, bones):
		lines_read = 0
		vert_count = 0

		self.bone_groups = [[] for i in repeat(None, len(bones))]

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
				self.verts = [Vertex() for i in range(vert_count)]
				break

		for vertex in self.verts:
			lines_read += vertex.__load_vert__(file, vert_count, self)

		return lines_read

	def __load_faces__(self, file):
		lines_read = 0
		face_count = 0

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
				self.faces = [Face(None,None) for i in range(face_count)]
				break
		
		for face in self.faces:
			lines_read += face.__load_face__(file, face_count)

		return lines_read

class Model(object):
	__slots__ = ('name', 'version', 'bones', 'meshes', 'materials')
	def __init__(self, name):
		self.name = name
		self.version = -1

		self.bones = []
		self.meshes = []
		self.materials = []

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
				self.meshes[index] = Mesh(line_split[2][1:-1])
				meshes_read += 1
				if meshes_read == mesh_count:
					return lines_read

		return lines_read

	# Generate actual submesh data from the default mesh
	def __generate_meshes__(self, default_mesh):
		bone_count = len(self.bones)
		mtl_count = len(self.materials)
		for mesh in self.meshes:
			mesh.bone_groups = [[] for i in range(bone_count)]
			mesh.material_groups = [[] for i in range(mtl_count)]

		# An array of vertex mappings for each mesh
		# used in the format vertex_map[mesh][original_vertex]
		# yields either None (unset) or the new vertex id
		vertex_map = [[None]*len(default_mesh.verts) for i in range(len(self.meshes))]

		for face in default_mesh.faces:
			mesh_id = face.mesh_id
			mtl_id = face.material_id
			mesh = self.meshes[mesh_id]
			for ind in face.indices:
				vert_id = vertex_map[mesh_id][ind.vertex]
				if vert_id is None:
					vert_id = len(mesh.verts)
					vertex_map[mesh_id][ind.vertex] = vert_id
					vert = default_mesh.verts[ind.vertex]
					mesh.verts.append(vert)
					for bone_id, weight in vert.weights:
						mesh.bone_groups[bone_id].append((vert_id, weight))
				ind.vertex = vert_id
				mesh.material_groups[mtl_id].append(vert_id)
			mesh.faces.append(face)

		# Remove duplicates
		for mesh in self.meshes:
			for group_index, group in enumerate(mesh.bone_groups):
				mesh.bone_groups[group_index] = list(set(group))
			for group_index, group in enumerate(mesh.material_groups):
				mesh.material_groups[group_index] = list(set(group))

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
		
		# A global mesh containing all of the vertex and face data for the entire model
		default_mesh = Mesh("$default")

		default_mesh.__load_verts__(file, self.bones)
		default_mesh.__load_faces__(file)
		
		self.__load_meshes__(file)
		self.__load_materials__(file)

		self.__generate_meshes__(default_mesh)

 		file.close()

	def WriteFile(self, path):
		file = open(path, "w")
		file.write("// Export time: %s\n\n" % strftime("%a %b %d %H:%M:%S %Y"))

		file.write("MODEL\n")
		file.write("VERSION %d\n\n" % self.version)
		
		# Bone Hierarchy
		file.write("NUMBONES %d\n" % len(self.bones))
		for bone_index, bone in enumerate(self.bones):
			file.write("BONE %d %d \"%s\"\n" % (bone_index, bone.parent, bone.name))
		file.write("\n")

		# Bone Transform Data
		for bone_index, bone in enumerate(self.bones):
			file.write("BONE %d\n" % bone_index)
			file.write("OFFSET %f %f %f\n" % (bone.offset[0], bone.offset[1], bone.offset[2]))
			file.write("SCALE %f %f %f\n" % (1.0, 1.0, 1.0))
			file.write("X %f %f %f\n" % bone.matrix[0])
			file.write("Y %f %f %f\n" % bone.matrix[1])
			file.write("Z %f %f %f\n\n" % bone.matrix[2])
		file.write("\n")

		# Vertices
		# Used to offset the vertex indices for each mesh
		vert_offsets = [0]
		for mesh in self.meshes:
			prev_index = len(vert_offsets) - 1
			vert_offsets.append(vert_offsets[prev_index] + len(mesh.verts))

		file.write("NUMVERTS %d\n" % vert_offsets[len(vert_offsets) - 1])
		for mesh_index, mesh in enumerate(self.meshes):
			for vert_index, vert in enumerate(mesh.verts):
				vert.save(file, vert_index + vert_offsets[mesh_index])

		# Faces
		face_count = sum([len(mesh.faces) for mesh in self.meshes])
		file.write("NUMFACES %d\n" % face_count)
		for mesh_index, mesh in enumerate(self.meshes):
			for face in mesh.faces:
				face.save(file, vert_offsets[mesh_index])

		# Meshes
		file.write("NUMOBJECTS %d\n" % len(self.meshes))
		for mesh_index, mesh in enumerate(self.meshes):
			file.write("OBJECT %d \"%s\"\n" % (mesh_index, mesh.name))
		file.write("\n")

		# Materials
		file.write("NUMMATERIALS %d\n" % len(self.materials))
		for material_index, material in enumerate(self.materials):
			material.save(file, material_index)


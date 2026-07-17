import math
import re
import cmath
import numbers
import copy

# TODO: add functions probably and also rref probs

def flatten_list(args):
    if not (isinstance(args, list) or isinstance(args, tuple)): return [args]
    out_args = []
    for arg in args:
        if isinstance(arg, list) or isinstance(arg, tuple):
            out_args += flatten_list(arg)
        else:
            out_args.append(arg)
    return list(out_args)

def conj(num):
    if isinstance(num, numbers.Real): return num
    return num.real - 1j * num.imag

def zero_one(dim, comp):
    return Vector(*[1 if i == comp else 0 for i in range(1, dim + 1)])

class Vector:
    components = []
    def __init__(self, *components):
        if len(components) == 0: raise Exception("No components in vector.")
        for component in components:
            if not isinstance(component, numbers.Number):
                raise Exception("Non number entry in vector.")
        self.components = components
    def __len__(self):
        return len(self.components)
    def __str__(self):
        return f"<{", ".join([str(component) for component in self.components])}>"
    def get(self, i):
        return self.components[i - 1]
    def add(self, vec):
        if len(self) != len(vec): raise Exception("Incompatible vectors to add.")
        return Vector(*[vec.get(i) + self.get(i) for i in range(1, len(self) + 1)])
    def sub(self, vec):
        if len(self) != len(vec): raise Exception("Incompatible vectors to subtract.")
        return self.add(vec.mult(-1))
    def mult(self, mult):
        if isinstance(mult, Matrix): return Matrix(self).mult(mult)
        return Vector(*[mult * self.get(i) for i in range(1, len(self) + 1)])
    def div(self, div):
        return Vector(*[self.get(i) / div for i in range(1, len(self) + 1)])
    def dot(self, vec):
        if len(self) != len(vec): raise Exception("Incompatible vectors to dot product.")
        return sum([vec.get(i + 1) * component for (i, component) in enumerate(self.components)])
    def cross(self, vec):
        if len(self) == 3 and len(vec) == 3:
            return Vector(
                self.get(2) * vec.get(3) - self.get(3) * vec.get(2),
                self.get(3) * vec.get(1) - self.get(1) * vec.get(3),
                self.get(1) * vec.get(2) - self.get(2) * vec.get(1),
            )
        elif len(self) == 2 and len(vec) == 2:
            return self.get(1) * vec.get(2) - self.get(2) * vec.get(1)
        else: raise Exception("Incompatible vectors to cross product.")
    def norm(self):
        return cmath.sqrt(sum([component * conj(component) for component in self.components]))

def eye(n):
    vectors = []
    for j in range(1, int(n) + 1):
        vectors.append(Vector(*[1 if i == j else 0 for i in range(1, int(n) + 1)]))
    return Matrix(*vectors)

def zeros(n):
    vectors = []
    for j in range(1, int(n) + 1):
        vectors.append(Vector(*[0 for i in range(1, int(n) + 1)]))
    return Matrix(*vectors)

def ones(n):
    vectors = []
    for j in range(1, int(n) + 1):
        vectors.append(Vector(*[1 for i in range(1, int(n) + 1)]))
    return Matrix(*vectors)

class Matrix:
    m = 0
    n = 0
    vectors = []

    def __init__(self, *vectors):
        vectors = copy.deepcopy(list(vectors))
        if len(vectors) == 1 and isinstance(vectors[0], Matrix):
            self.vectors = vectors[0].vectors
            self.m = vectors[0].m
            self.n = vectors[0].n
            return
        if len(vectors) == 0: raise Exception("Matrix doesn't have any vectors.")
        if not isinstance(vectors[0], Vector):
            self.init_with_rowvectors(*vectors)
            return
        m = len(vectors[0])
        n = len(vectors)
        for i, vector in enumerate(vectors):
            if not isinstance(vector, Vector):
                vectors[i] = Vector(*flatten_list(vector))
            if len(vectors[i]) != m:
                raise Exception("Matrix constructed with vectors of different dimensions.")
        self.vectors = vectors
        self.m = m
        self.n = n

    def __str__(self):
        return f"[{", ".join([str(vector) for vector in self.vectors])}]"
    
    def init_with_rowvectors(self, *row_vectors):
        if isinstance(row_vectors[0], numbers.Number):
            matrix = Matrix(*[Vector(row_vector) for row_vector in row_vectors])
            self.m = matrix.m
            self.n = matrix.n
            self.vectors = copy.deepcopy(matrix.vectors)
            return
        else:
            new_row_vectors = []
            for row_vector in row_vectors:
                for i in range(1, row_vector.m + 1):
                    new_row_vectors.append(row_vector.row(i))
            row_vectors = new_row_vectors
        m = len(row_vectors)
        n = len(row_vectors[0].vectors)
        vectors = []
        for i in range(0, m):
            if len(row_vectors[i].vectors) != n: raise Exception("Matrix constructed with row vectors of different dimensions.")
        for j in range(1, n + 1):
            vectors.append(Vector(*[row_vectors[i].get(1, j) for i in range(m)]))
        self.vectors = vectors
        self.m = m
        self.n = n
    
    def get(self, i, j):
        return self.vectors[j - 1].get(i)
    
    def basis(self, j):
        return self.vectors[j - 1]
    
    def add(self, matrix):
        if self.n != matrix.n or self.m != matrix.m: raise Exception("Incompatible matrices to add.")
        return Matrix(*[vector.add(matrix.basis(i + 1)) for i, vector in enumerate(self.vectors)])
    
    def sub(self, matrix):
        if self.n != matrix.n or self.m != matrix.m: raise Exception("Incompatible matrices to subtract.")
        return Matrix(*[vector.sub(matrix.basis(i + 1)) for i, vector in enumerate(self.vectors)])
    
    def div(self, div):
        return Matrix(*[vector.div(div) for vector in self.vectors])

    def mult(self, multiplicand):
        if isinstance(multiplicand, numbers.Number):
            return Matrix(*[vector.mult(multiplicand) for vector in self.vectors])
        if isinstance(multiplicand, Vector):
            vector = multiplicand
            if len(vector) != self.n: raise Exception("Incompatible matrix multiplication")
            return Vector(*[sum([self.get(i, j) * vector.get(j) for j in range(1, len(vector) + 1)]) for i in range(1, self.m + 1)])
        elif isinstance(multiplicand, Matrix):
            matrix = multiplicand
            return Matrix(*[self.mult(vector) for vector in matrix.vectors])

    def power(self, power):
        if power % 1 != 0: raise Exception("Non-integer power.")
        if power <= 0 and self.m != self.n: raise Exception("Identity matrix and inverse matrices are not defined for non-squares.")
        if power == 0: return eye(self.n)
        if power < 0: return self.power(-power).inverse()
        return self.power(power - 1).mult(self)

    def minor(self, i, j):
        cofactor_matrix_vectors = self.vectors[:j - 1] + self.vectors[j:]
        for j, cofactor_vector in enumerate(cofactor_matrix_vectors):
            cofactor_matrix_vectors[j] = Vector(*(cofactor_vector.components[:i - 1] + cofactor_vector.components[i:]))
        return Matrix(*cofactor_matrix_vectors)
    
    def cofactor(self):
        vector_list = []
        for j in range(1, self.n + 1):
            component_list = []
            for i in range(1, self.m + 1):
                minor = self.minor(i, j)
                sign = (-1) ** (i + j)
                component_list.append(minor.det() * sign)
            vector_list.append(Vector(*component_list))
        return Matrix(*vector_list)

    def inverse(self):
        determinant = self.det()
        if determinant == 0: raise Exception("Cannot invert singular matrix.")
        return self.cofactor().transpose().div(determinant)

    def det(self):
        if self.m != self.n: raise Exception("Determinant isn't defined for m != n")
        if self.m == self.n == 1: return self.get(1, 1)
        determinant = 0
        for i in range(1, self.n + 1):
            sign = 2 * (i % 2) - 1
            cofactor_matrix_vectors = self.vectors[:i - 1] + self.vectors[i:]
            for j, cofactor_vector in enumerate(cofactor_matrix_vectors):
                cofactor_matrix_vectors[j] = Vector(*cofactor_vector.components[1:])
            determinant += self.get(1, i) * sign * Matrix(*cofactor_matrix_vectors).det()
        return determinant
    
    def trace(self):
        if self.m != self.n: raise Exception("Determinant isn't defined for m != n")
        trace = 0
        for i in range(1, self.m + 1):
            trace += self.get(i, i)
        return trace
    
    def transpose(self):
        transpose_vectors = []
        for j in range(1, self.n + 1):
            transpose_vectors.append(Vector(*[self.get(j, i) for i in range(1, self.m + 1)]))
        return Matrix(*transpose_vectors)
    
    def transpose_conj(self):
        transpose_vectors = []
        for j in range(1, self.n + 1):
            transpose_vectors.append(Vector(*[conj(self.get(j, i)) for i in range(1, self.m + 1)]))
        return Matrix(*transpose_vectors)

    def rref(self):
        rref = self
        pivot_row = 1
        # finish
        for j in range(1, rref.n + 1):
            if pivot_row > rref.m: break
            pivot_found = False
            if rref.get(pivot_row, j) != 0: pivot_found = True
            else:
                # find non zero in the column > pivot_row
                new_pivot_row = pivot_row + 1
                while new_pivot_row <= rref.m:
                    if rref.get(new_pivot_row, j) != 0:
                        pivot_found = True
                        # swap rows
                        # i know this permutation matrix defn is long but no one has to see it
                        perm_mat = Matrix(*[zero_one(rref.m, new_pivot_row if j == pivot_row else pivot_row if j == new_pivot_row else j) for j in range(1, rref.m + 1)])
                        rref = perm_mat.mult(rref)
                        break
                    new_pivot_row += 1
            if not pivot_found:
                # pivot_row += 1
                continue
            elim_vec_components = []
            pivot = rref.get(pivot_row, j)
            for i in range(1, rref.m + 1):
                elim_vec_components.append((1 if i == pivot_row else -rref.get(i, j)) / pivot)
            elim_vector = Vector(*elim_vec_components)
            # print(str(elim_vector))
            # elim_vector = rref.basis(j).div(pivot)
            # print(*[1 if i == 2 else 0 for i in range(1, self.m)])
            elim_mat = Matrix(*[elim_vector if elim_j == pivot_row else zero_one(rref.m, elim_j) for elim_j in range(1, rref.m + 1)])
            rref = elim_mat.mult(rref)
            pivot_row += 1
        return rref

    def row(self, i):
        return Matrix(*[self.get(i, j) for j in range(1, self.n + 1)])

def multiply(a, b):
    if isinstance(a, numbers.Number) and isinstance(b, numbers.Number): return a * b
    if isinstance(a, Vector) and isinstance(b, Vector): return a.dot(b)
    if isinstance(a, numbers.Number): return b.mult(a)
    else: return a.mult(b)
def power(a, b):
    if isinstance(a, numbers.Number): return a ** b
    else: return a.power(b)
def add(a, b):
    if isinstance(a, numbers.Number): return a + b
    else: return a.add(b)
def sub(a, b):
    if isinstance(a, numbers.Number): return a - b
    else: return a.sub(b)

def semicolon(*args):
    matrices = []
    for arg in args:
        # print(arg)
        if isinstance(arg, Matrix):
            matrices.append(arg)
        elif (isinstance(arg, list) or isinstance(arg, tuple)) and len(arg) != 0 and isinstance(arg[0], Matrix):
            matrices.append(*flatten_list(arg))
        elif (isinstance(arg, list) or isinstance(arg, tuple)) and len(arg) != 0:
            matrices.append(Matrix(*flatten_list(arg)))
        else:
            matrices.append(Matrix(arg))
    return Matrix(*matrices)
def arg(z):
    if abs(z) == 0: return 0
    phi = (cmath.log(z / abs(z)) / 1j).real
    if phi < 0: phi += 2 * math.pi
    return phi

syntax_error = '6767mangomangomustardd'
math_error = 'whatthehellysabcdefiefhei'

pre_operator = 1 # where the operator is before its argument, eg. sin(x), sqrt(x)
post_operator = 2 # where the operator is after its argument, eg. x!
in_operator = 3 # where the operator is in between its 2 arguments, eg. x + y
bracket_operator = 4 # where the operator surrounds its argument, eg. <x, y>
blank_operator = 5 # where the operator just doesnt exist, eg. xy
# note that pre operators are evaluated first, so sin2! == (sin 2)!

openers = ['(', '[', '<']
closers = [')', ']', '>']

operators = {
    ',': {'type': in_operator, 'rank': -1, 'func': lambda *args: args, 'list_op': True},

    # basic operators
    '+': {'type': in_operator, 'rank': 0, 'func': lambda a, b: add(a, b)},
    '-': {'type': in_operator, 'rank': 0, 'func': lambda a, b: sub(a, b)},
    '*': {'type': in_operator, 'rank': 1, 'func': lambda a, b: multiply(a, b)},
    '': {'type': blank_operator, 'rank': 1, 'func': lambda a, b: multiply(a, b)},
    '/': {'type': in_operator, 'rank': 1, 'func': lambda a, b: multiply(a, 1 / b)},
    '%': {'type': in_operator, 'rank': 1, 'func': lambda a, b: a % b},
    '^': {'type': in_operator, 'rank': 2, 'func': lambda a, b: power(a, b)},
    # basic funcs
    '!': {'type': post_operator, 'func': lambda a: math.gamma(1 + a)},
    'ln': {'type': pre_operator, 'func': lambda a: cmath.log(a)},
    'logb': {'type': pre_operator, 'func': lambda a: cmath.log2(a)},
    'log': {'type': pre_operator, 'func': lambda a: cmath.log10(a)},
    'exp': {'type': pre_operator, 'func': lambda a: cmath.exp(a)},
    'sqrt': {'type': pre_operator, 'func': lambda a: cmath.sqrt(a)},
    'cbrt': {'type': pre_operator, 'func': lambda a: cmath.cbrt(a)},
    'sign': {'type': pre_operator, 'func': lambda a: a / abs(a)},
    'sgn': {'type': pre_operator, 'func': lambda a: a / abs(a)},
    'abs': {'type': pre_operator, 'func': lambda a: abs(a)},
    'arg': {'type': pre_operator, 'func': lambda a: arg(a)},
    'conj': {'type': pre_operator, 'func': lambda a: conj(a)},
    'hyp': {'type': pre_operator, 'func': lambda *args: cmath.sqrt(sum([arg*conj(arg) for arg in args])), 'list_op': True},
    # matrices + vectors
    'eye': {'type': pre_operator, 'func': lambda a: eye(a)},
    'zeros': {'type': pre_operator, 'func': lambda a: zeros(a)},
    'ones': {'type': pre_operator, 'func': lambda a: ones(a)},
    'det': {'type': pre_operator, 'func': lambda a: a.det()},
    'trace': {'type': pre_operator, 'func': lambda a: a.trace()},
    'tr': {'type': pre_operator, 'func': lambda a: a.trace()},
    'rref': {'type': pre_operator, 'func': lambda a: a.rref()},
    'T': {'type': pre_operator, 'func': lambda a: a.transpose()},
    'transpose': {'type': pre_operator, 'func': lambda a: a.transpose()},
    '&': {'type': in_operator, 'rank': 1, 'func': lambda a, b: a.cross(b)},
    '< >': {'type': bracket_operator, 'func': lambda *args: Vector(*args), 'list_op': True},
    '[ ]': {'type': bracket_operator, 'func': lambda *args: Matrix(*args), 'list_op': True},
    ';': {'type': in_operator, 'rank': -2, 'func': lambda *args: semicolon(*args)}, # not included in list op bc umm it kinda needs them
    # trig + hyperbolic trig stuffs
    'sin': {'type': pre_operator, 'func': lambda a: cmath.sin(a)},
    'cos': {'type': pre_operator, 'func': lambda a: cmath.cos(a)},
    'tan': {'type': pre_operator, 'func': lambda a: cmath.tan(a)},
    'sec': {'type': pre_operator, 'func': lambda a: 1 / cmath.cos(a)},
    'csc': {'type': pre_operator, 'func': lambda a: 1 / cmath.sin(a)},
    'cot': {'type': pre_operator, 'func': lambda a: 1 / cmath.tan(a)},
    'sinh': {'type': pre_operator, 'func': lambda a: cmath.sinh(a)},
    'cosh': {'type': pre_operator, 'func': lambda a: cmath.cosh(a)},
    'tanh': {'type': pre_operator, 'func': lambda a: cmath.tanh(a)},
    'sech': {'type': pre_operator, 'func': lambda a: 1 / cmath.cosh(a)},
    'csch': {'type': pre_operator, 'func': lambda a: 1 / cmath.sinh(a)},
    'coth': {'type': pre_operator, 'func': lambda a: 1 / cmath.tanh(a)},
    'asin': {'type': pre_operator, 'func': lambda a: cmath.asin(a)},
    'acos': {'type': pre_operator, 'func': lambda a: cmath.acos(a)},
    'atan': {'type': pre_operator, 'func': lambda a: cmath.atan(a)},
    'asec': {'type': pre_operator, 'func': lambda a: cmath.acos(1 / a)},
    'acsc': {'type': pre_operator, 'func': lambda a: cmath.asin(1 / a)},
    'acot': {'type': pre_operator, 'func': lambda a: cmath.atan(1 / a)},
    'asinh': {'type': pre_operator, 'func': lambda a: cmath.asinh(a)},
    'acosh': {'type': pre_operator, 'func': lambda a: cmath.acosh(a)},
    'atanh': {'type': pre_operator, 'func': lambda a: cmath.atanh(a)},
    'asech': {'type': pre_operator, 'func': lambda a: cmath.acosh(1 / a)},
    'acsch': {'type': pre_operator, 'func': lambda a: cmath.asinh(1 / a)},
    'acoth': {'type': pre_operator, 'func': lambda a: cmath.atanh(1 / a)},
    'arcsin': {'type': pre_operator, 'func': lambda a: cmath.asin(a)},
    'arccos': {'type': pre_operator, 'func': lambda a: cmath.acos(a)},
    'arctan': {'type': pre_operator, 'func': lambda a: cmath.atan(a)},
    'arcsec': {'type': pre_operator, 'func': lambda a: cmath.acos(1 / a)},
    'arccsc': {'type': pre_operator, 'func': lambda a: cmath.asin(1 / a)},
    'arccot': {'type': pre_operator, 'func': lambda a: cmath.atan(1 / a)},
    'arcsinh': {'type': pre_operator, 'func': lambda a: cmath.asinh(a)},
    'arccosh': {'type': pre_operator, 'func': lambda a: cmath.acosh(a)},
    'arctanh': {'type': pre_operator, 'func': lambda a: cmath.atanh(a)},
    'arcsech': {'type': pre_operator, 'func': lambda a: cmath.acosh(1 / a)},
    'arccsch': {'type': pre_operator, 'func': lambda a: cmath.asinh(1 / a)},
    'arccoth': {'type': pre_operator, 'func': lambda a: cmath.atanh(1 / a)},
}

constants = {
    'e': cmath.e,
    'pi': cmath.pi,
    'i': 'j'
}

def isnum(string):
    string = str.lower(string)
    if string == '': return False
    if string[0] == '-': string = string[1:]
    if string == '': return False
    if string == 'j': return True
    if string[-1] == 'j': string = string[:-1]
    if string == '.': return False
    match = re.findall(r'([^.]*)\.*', string)
    if len(match) > 3: return False
    return str.isdecimal(match[0]) and (len(match) == 2 or str.isdecimal(match[1]))

def tonum(string): # note that there are no operators in ts
    if string == 'j':
        return 1j
    if string == '-j':
        return -1j
    if string[-1] == 'j':
        return float(string[:-1]) * 1j
    else:
        return float(string)

def parse(input):
    # print(input)
    if input == '':
        print('error a')
        return syntax_error
    if (isnum(input)): return tonum(input)
    nest_count = 0
    potential_operators = []
    for i, char in enumerate(input): # inoperator parser
        if char in openers: nest_count += 1
        elif char in closers: nest_count -= 1
        prev_char = input[i - 1] if i >= 1 else ''
        if nest_count == 0 and char in operators and operators[char]['type'] == in_operator:
            if char == '-':
                if i == 0: continue # prevents the '-' in '-3' from becoming an oeprator
                if not (isnum(prev_char) or prev_char == '.' or prev_char in closers): continue # makes sometrhing like (2)-3 become operator
            potential_operators.append((i, char))
        elif nest_count == 0 and char in closers and i < len(input) - 1 and input[i + 1] not in operators: # checks for things like (3)2
            potential_operators.append((i + 1, ''))
        elif nest_count == 1 and i >= 1 and char in openers: # checks for things olike 2(3)
            paren_mult = True
            for operator_name, operator in operators.items():
                if operator['type'] != pre_operator and operator['type'] != in_operator: continue
                if len(operator_name) > i + 1: continue
                if input[i - len(operator_name):i] == operator_name:
                    paren_mult = False
                    break
            # print(paren_mult)
            if paren_mult:
                potential_operators.append((i, ''))
        elif nest_count == 0 and i >= 1 and i < len(input) - 1:
            paren_mult = True
            for operator_name, operator in operators.items():
                if operator['type'] != in_operator: continue
                if len(operator_name) > i: continue
                if input[i - len(operator_name):i] == operator_name:
                    paren_mult = False
            if paren_mult == True:
                for operator_name, operator in operators.items():
                    if operator['type'] != pre_operator: continue
                    if len(operator_name) >= len(input) - i: continue
                    if input[i:i + len(operator_name)] == operator_name:
                        potential_operators.append((i, ''))
                        break

    if nest_count != 0:
        print('error b')
        return syntax_error
    if potential_operators == []: # other operators parser (only if there are no inoperators)
        if input[0] == '(' and input[-1] == ')':
            return parse(input[1:-1])
        elif input[0] == '-':
            # print(input)
            return parse(f'-1*({input[1:]})')
        else:
            match = re.findall(r'^[a-zA-Z]+', input)
            pre_match = match[0] if len(match) >= 1 else None
            match = re.findall(r'!$', input)
            post_match = match[0] if len(match) >= 1 else None
            if post_match:
                operator = operators.get(post_match)
                print(operator)
                if operator and operator['type'] == post_operator:
                    return {
                        'operator': operator,
                        'args': [parse(input[:-len(post_match)])]
                    }
                # for operator_name, operator in operators.items():
                #     if operator_name == '': continue
                #     if operator['type'] == post_operator and post_match == operator_name:
                #         return {
                #             'operator': operator,
                #             'args': [parse(input[:-len(operator_name)])]
                #         }
            if pre_match:
                operator = operators.get(pre_match)
                if operator and operator['type'] == pre_operator:
                    return {
                        'operator': operator,
                        'args': [parse(input[len(pre_match):])]
                    }
            #     for operator_name, operator in operators.items():
            #         if operator_name == '': continue
            #         if operator['type'] == pre_operator and pre_match == operator_name:
            #             return {
            #                 'operator': operator,
            #                 'args': [parse(input[len(operator_name):])]
            #             }

            bracket_match = input[0] + " " + input[-1]
            operator = operators.get(bracket_match)
            if operator:
                return {
                    'operator': operator,
                    'args': [parse(input[1:-1])]
                }
            # for operator_name, operator in operators.items():
            #     if operator_name == '': continue
            #     # print(operator_name, input[0], input[-1])
            #     if operator['type'] == bracket_operator and input[0] == operator_name[0] and input[-1] == operator_name[-1]:
            #         return {
            #             'operator': operator,
            #             'args': [parse(input[1:-1])]
            #         }

            print('error c')
            return syntax_error
    
    operator = potential_operators[0]
    for index, char in potential_operators: # selects best operator via pemdas
        if operators[char]['rank'] <= operators[operator[1]]['rank']:
            operator = (index, char)

    return {
        'operator': operators[operator[1]],
        'args': [parse(input[:operator[0]]), parse(input[operator[0] + len(operator[1]):])],
    }

def replace_vars(input, vars):
    for name, value in vars.items():
        input = re.sub(r'(?<![a-zA-Z_])' + name + r'(?![a-zA-Z_])', f'({value})', input)
    for name, value in constants.items():
        input = re.sub(r'(?<![a-zA-Z_])' + name + r'(?![a-zA-Z_])', f'({value})', input)
    return input

def evaluate(expression):
    if expression == syntax_error: return syntax_error
    if expression == math_error: return math_error
    if isinstance(expression, numbers.Number): return expression
    operator = expression['operator']
    operator_type = operator['type']
    operator_func = operator['func']
    arguments = []
    for expression_argument in expression['args']:
        argument = evaluate(expression_argument)
        if argument == syntax_error: return syntax_error
        arguments.append(argument)
    for operator_name, list_operator in operators.items():
        if not list_operator.get('list_op'): continue
        if list_operator != operator: continue
        arguments = flatten_list(arguments)
    # if operator == operators[',']:
    #     arguments = flatten_list(arguments)
    # elif operator == operators[';']:
    #     for i, arg in enumerate(arguments):
    #         arguments[i] = flatten_list(arg)

    try:
        return operator_func(*arguments)
    except Exception as e:
        print(e)
        return math_error
    
def calculate(input, vars):
    input = re.sub(r'\s', '', replace_vars(input, vars))
    # print(input)
    expression = parse(input)
    return evaluate(expression)

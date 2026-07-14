import re
import math
import numbers

import numpy

# TODO: add lists stuff

syntax_error = '6767mangomangomustardd'
math_error = 'whatthehellysabcdefiefhei'

pre_operator = 1 # where the operator is before its argument, eg. sin(x), sqrt(x)
post_operator = 2 # where the operator is after its argument, eg. x!
in_operator = 3 # where the operator is in between its 2 arguments, eg. x + y
bracket_operator = 4 # where the operator surrounds its argument, eg. |x|
blank_operator = 5 # where the operator just doesnt exist, eg. xy
# note that pre operators are evaluated first, so sin2! == (sin 2)!
operators = {
    # basic operators
    '+': {'type': in_operator, 'rank': 0, 'func': lambda a, b: a + b},
    '-': {'type': in_operator, 'rank': 0, 'func': lambda a, b: a - b},
    '*': {'type': in_operator, 'rank': 1, 'func': lambda a, b: a * b},
    '': {'type': blank_operator, 'rank': 1, 'func': lambda a, b: a * b},
    '/': {'type': in_operator, 'rank': 1, 'func': lambda a, b: a / b},
    '%': {'type': in_operator, 'rank': 1, 'func': lambda a, b: a % b},
    '^': {'type': in_operator, 'rank': 2, 'func': lambda a, b: a ** b},
    # basic funcs
    '!': {'type': post_operator, 'func': lambda a: math.gamma(1 + a)},
    'ln': {'type': pre_operator, 'func': lambda a: math.log(a)},
    'logb': {'type': pre_operator, 'func': lambda a: math.log2(a)},
    'log': {'type': pre_operator, 'func': lambda a: math.log10(a)},
    'exp': {'type': pre_operator, 'func': lambda a: math.e ** a},
    'sqrt': {'type': pre_operator, 'func': lambda a: math.sqrt(a)},
    'cbrt': {'type': pre_operator, 'func': lambda a: math.cbrt(a)},
    'sign': {'type': pre_operator, 'func': lambda a: a / abs(a)},
    'sgn': {'type': pre_operator, 'func': lambda a: a / abs(a)},
    'abs': {'type': pre_operator, 'func': lambda a: abs(a)},
    # trig + hyperbolic trig stuffs
    'sin': {'type': pre_operator, 'func': lambda a: math.sin(a)},
    'cos': {'type': pre_operator, 'func': lambda a: math.cos(a)},
    'tan': {'type': pre_operator, 'func': lambda a: math.tan(a)},
    'sec': {'type': pre_operator, 'func': lambda a: 1 / math.cos(a)},
    'csc': {'type': pre_operator, 'func': lambda a: 1 / math.sin(a)},
    'cot': {'type': pre_operator, 'func': lambda a: 1 / math.tan(a)},
    'sinh': {'type': pre_operator, 'func': lambda a: math.sinh(a)},
    'cosh': {'type': pre_operator, 'func': lambda a: math.cosh(a)},
    'tanh': {'type': pre_operator, 'func': lambda a: math.tanh(a)},
    'sech': {'type': pre_operator, 'func': lambda a: 1 / math.cosh(a)},
    'csch': {'type': pre_operator, 'func': lambda a: 1 / math.sinh(a)},
    'coth': {'type': pre_operator, 'func': lambda a: 1 / math.tanh(a)},
    'asin': {'type': pre_operator, 'func': lambda a: math.asin(a)},
    'acos': {'type': pre_operator, 'func': lambda a: math.acos(a)},
    'atan': {'type': pre_operator, 'func': lambda a: math.atan(a)},
    'asec': {'type': pre_operator, 'func': lambda a: math.acos(1 / a)},
    'acsc': {'type': pre_operator, 'func': lambda a: math.asin(1 / a)},
    'acot': {'type': pre_operator, 'func': lambda a: math.atan(1 / a)},
    'asinh': {'type': pre_operator, 'func': lambda a: math.asinh(a)},
    'acosh': {'type': pre_operator, 'func': lambda a: math.acosh(a)},
    'atanh': {'type': pre_operator, 'func': lambda a: math.atanh(a)},
    'asech': {'type': pre_operator, 'func': lambda a: math.acosh(1 / a)},
    'acsch': {'type': pre_operator, 'func': lambda a: math.asinh(1 / a)},
    'acoth': {'type': pre_operator, 'func': lambda a: math.atanh(1 / a)},
    'arcsin': {'type': pre_operator, 'func': lambda a: math.asin(a)},
    'arccos': {'type': pre_operator, 'func': lambda a: math.acos(a)},
    'arctan': {'type': pre_operator, 'func': lambda a: math.atan(a)},
    'arcsec': {'type': pre_operator, 'func': lambda a: math.acos(1 / a)},
    'arccsc': {'type': pre_operator, 'func': lambda a: math.asin(1 / a)},
    'arccot': {'type': pre_operator, 'func': lambda a: math.atan(1 / a)},
    'arcsinh': {'type': pre_operator, 'func': lambda a: math.asinh(a)},
    'arccosh': {'type': pre_operator, 'func': lambda a: math.acosh(a)},
    'arctanh': {'type': pre_operator, 'func': lambda a: math.atanh(a)},
    'arcsech': {'type': pre_operator, 'func': lambda a: math.acosh(1 / a)},
    'arccsch': {'type': pre_operator, 'func': lambda a: math.asinh(1 / a)},
    'arccoth': {'type': pre_operator, 'func': lambda a: math.atanh(1 / a)},
}

constants = {
    'e': math.e,
    'pi': math.pi,
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
        # print('error a')
        return syntax_error
    if (isnum(input)): return tonum(input)
    nest_count = 0
    potential_operators = []
    for i, char in enumerate(input):
        if char == '(': nest_count += 1
        elif char == ')': nest_count -= 1
        prev_char = input[i - 1] if i >= 1 else ''
        if nest_count == 0 and char in operators and operators[char]['type'] == in_operator:
            if not (char == '-' and (i == 0 or not (str.isdecimal(prev_char) or prev_char == '.'))): # prevents the '-' in '-3' from becoming an oeprator
                potential_operators.append((i, char))
        elif nest_count == 0 and char == ')' and i < len(input) - 1 and input[i + 1] not in operators: # checks for things like 2(3) and (3)2
            potential_operators.append((i + 1, '*'))
        elif nest_count == 1 and i >= 1 and char == '(' and prev_char:
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
        # print('error b')
        return syntax_error
    if potential_operators == []:
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
            for operator_name, operator in operators.items():
                if operator_name == '': continue
                if operator['type'] == post_operator and post_match and post_match == operator_name:
                    return {
                        'operator': operator,
                        'args': [parse(input[:-len(operator_name)])]
                    }
            for operator_name, operator in operators.items():
                if operator_name == '': continue
                if operator['type'] == pre_operator and pre_match and pre_match == operator_name:
                    return {
                        'operator': operator,
                        'args': [parse(input[len(operator_name):])]
                    }

            # print('error c')
            return syntax_error
    
    operator = potential_operators[0]
    for index, char in potential_operators:
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
    try:
        return operator_func(*arguments)
    except:
        return math_error
    
def calculate(input, vars):
    input = re.sub(r'\s', '', replace_vars(input, vars))
    print(input)
    expression = parse(input)
    return evaluate(expression)

# while True:
#     print(calculate(input('calculate: '), {}))
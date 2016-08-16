"""Convert cvxpy LinOp expression trees to TensorFlow graphs."""

import numpy as np
import cvxpy as cvx
import tensorflow as tf

def sum_dicts(dicts):
    sum_dict = {}
    for val_dict in dicts:
        for id_, value in val_dict.items():
            if id_ in sum_dict:
                sum_dict[id_] = sum_dict[id_] + value
            else:
                sum_dict[id_] = value
    return sum_dict

def is_scalar(x):
    for dim in x.get_shape():
        if dim != 1:
            return False
    return True

def tensor(lin_op, value_map={}):
    f_name = "tensor_" + lin_op.type
    return globals()[f_name](lin_op, value_map)

def tensor_mul(lin_op, value_map):
    a = tensor(lin_op.data, value_map)
    b = tensor(lin_op.args[0], value_map)
    if is_scalar(a) or is_scalar(b):
        return tf.mul(a, b)
    else:
        return tf.matmul(a, b)

def tensor_sum(lin_op, value_map):
    if len(lin_op.args) == 1:
        # special case for single arg sum
        return tensor(lin_op.args[0], value_map)

    return tf.add(
        tensor(lin_op.args[0], value_map),
        tensor(lin_op.args[1], value_map))

def tensor_neg(lin_op, value_map):
    return tf.neg(
        tensor(lin_op.args[0], value_map))

def tensor_promote(lin_op, value_map):
    # NOTE(mwytock): promotion handled directly in mul and add
    return tensor(lin_op.args[0], value_map)

def tensor_dense_const(lin_op, value_map):
    return tf.constant(lin_op.data, dtype=tf.float64)

def tensor_scalar_const(lin_op, value_map):
    return tf.constant(lin_op.data, dtype=tf.float64)

def tensor_variable(lin_op, value_map):
    var_id = lin_op.data
    return value_map[var_id]

def adjoint_tensor(lin_op, value):
    f_name = "adjoint_tensor_" + lin_op.type
    return globals()[f_name](lin_op, value)

def adjoint_tensor_mul(lin_op, value):
    a = tensor(lin_op.data)
    b = value
    if is_scalar(a):
        c = tf.mul(a, b)
    elif is_scalar(b):
        c = tf.mul(tf.transpose(a), b)
    else:
        c = tf.matmul(a, b, transpose_a=True)
    return adjoint_tensor(lin_op.args[0], c)

def adjoint_tensor_neg(lin_op, value):
    return adjoint_tensor(lin_op.args[0], -value)

def adjoint_tensor_sum(lin_op, value):
    return sum_dicts(adjoint_tensor(arg, value) for arg in lin_op.args)

def adjoint_tensor_variable(lin_op, value):
    var_id = lin_op.data
    return {var_id: value}

from flask import jsonify

def ERROR_RESPONSE(ERROR, STATUSCODE,MSG):
    errorResponse = {"Error": ERROR,"Message":MSG}
    return jsonify(errorResponse), STATUSCODE


def SUCCESS_RESPONSE(CONTENT, STATUSCODE):
    successResponse = {"Message": CONTENT}
    return jsonify(successResponse), STATUSCODE
#include <Python.h>
#include <numpy/arrayobject.h>
#include "micropather.h"
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <exception>
#include <cassert>
#include <iostream>

using namespace micropather;

class Matrix : public Graph {
	public:
	Matrix(PyObject* o) {
		mat = PyArray_FROMANY(o, NPY_FLOAT64,2,2, NPY_CARRAY);
		
		if (mat == NULL) {
			PyErr_SetString(PyExc_ValueError, "Expected a float64 matrix");
			return;
		}
		Py_INCREF(mat);
		
		cols = PyArray_DIM(mat, 1);
		rows = PyArray_DIM(mat, 0);
		
	}

	~Matrix() {
		Py_DECREF(mat);
	}

	void setMat(PyObject* o) {
		PyObject* tmp = PyArray_FROMANY(o, NPY_FLOAT64,2,2, NPY_CARRAY);
		if (tmp == NULL) {
			PyErr_SetString(PyExc_ValueError, "Expected a float64 matrix");
			return;
		}
		Py_DECREF(mat);
		mat = tmp;
		Py_INCREF(mat);
		
		cols = PyArray_DIM(mat, 1);
		rows = PyArray_DIM(mat, 0);
	}

	void NodeToXY( void* node, int* row, int* col ) 
	{
		int index = (MP_UPTR)node;
		
		int r = index / cols;
		while (r < 0)
			r = r + rows;
		while (r >= rows)
			r = r - rows;
		int c = index - r * cols;
		while (c < 0)
			c = c + cols;
		while (c >= cols)
			c = c - cols;

		*row = r;
		*col = c;
	}

	void* XYToNode( int r, int c )
	{
		while (r < 0)
			r = rows + r;
		while (r >= rows)
			r = r - rows;
		while (c < 0)
			c = cols + c;
		while (c >= cols)
			c = c - cols;
		
		return (void*) ( r*cols+ c );
	}
	
	double mat_cost(int r, int c) {
		while (r < 0)
			r = rows + r;
		while (r >= rows)
			r = r - rows;
		while (c < 0)
			c = cols + c;
		while (c >= cols)
			c = c - cols;
		
		double* value = (double*)PyArray_GETPTR2(mat,r, c);
		double cost = double(*value);
		return cost;
	}

	virtual float LeastCostEstimate( void* stateStart, void* stateEnd ) {
		using std::min;

		int row1, col1, row2, col2;

		NodeToXY(stateStart, &row1, &col1);
		NodeToXY(stateEnd, &row2, &col2);
		
		int d_col = min(abs(col1 - col2), cols - abs(col1 - col2));
		int d_row = min(abs(row1 - row2), rows - abs(row1 - row2));
        	return d_row + d_col;
	}
	
	virtual void AdjacentCost( void* node, std::vector< StateCost > *neighbors ) 
	{
		int x, y;
		const int dx[4] = { 1, 0, -1, 0, };
		const int dy[4] = { 0, 1,  0,-1, };

		NodeToXY( node, &x, &y );

		for( int i=0; i<4; ++i ) {
			int nx = x + dx[i];
			int ny = y + dy[i];

			double c = mat_cost( nx, ny );
			if ( c > 0 ) {
				StateCost nodeCost = { XYToNode( nx, ny ), 
							c };
				neighbors->push_back( nodeCost );
			}
		}
	}
	virtual void PrintStateInfo( void* state ) {
		
	}

	private:
	PyObject* mat;
	int rows, cols;
};

class AstarMatrix : public MicroPather {
	public:
	AstarMatrix(Matrix *graph, unsigned allocate, unsigned typicalAdjacent) : 
		MicroPather(graph, allocate, typicalAdjacent) 
	{matrix = graph;}

	PyObject* solve(PyObject* start, PyObject* goal) {

		if (!PySequence_Check(start)) {
			PyErr_SetString(PyExc_ValueError, "start has to be a tuple-like");
			return NULL;
		}
		if (!PySequence_Check(goal)) {
			PyErr_SetString(PyExc_ValueError, "goal has to be a tuple-like");
			return NULL;
		}
		
		PyObject *val;
		val = PySequence_GetItem(start, 0);
		if (val == NULL) {
			PyErr_SetString(PyExc_ValueError, "Error accessing element 0 of start");
			return NULL;
		}
		int row1 = PyInt_AsLong(val);

		val = PySequence_GetItem(start, 1);
		if (val == NULL) {
			PyErr_SetString(PyExc_ValueError, "Error accessing element 1 of start");
			return NULL;
		}
		int col1 = PyInt_AsLong(val);

		val = PySequence_GetItem(goal, 0);
		if (val == NULL) {
			PyErr_SetString(PyExc_ValueError, "Error accessing element 0 of goal");
			return NULL;
		}
		int row2 = PyInt_AsLong(val);

		val = PySequence_GetItem(goal, 1);
		if (val == NULL) {
			PyErr_SetString(PyExc_ValueError, "Error accessing element 0 of goal");
			return NULL;
		}
		int col2 = PyInt_AsLong(val);

		void* start_state = matrix->XYToNode(row1, col1);
		void* end_state = matrix->XYToNode(row2, col2);

		float total_cost = 0;
		int res = MicroPather::Solve(start_state, 
					     end_state,
					     &path,
					     &total_cost);
		PyObject* found_path;
		PyObject* tuple_element;
		PyObject* tuple_ret;

		tuple_ret = PyTuple_New(2);
		PyTuple_SetItem(tuple_ret,1,PyFloat_FromDouble(total_cost));

		if (res == NO_SOLUTION) {
			PyTuple_SetItem(tuple_ret, 0, PyList_New(0));
			return tuple_ret;
		}

		found_path = PyList_New(path.size());
		
		Py_ssize_t pos = 0;
		for (std::vector<void*>::iterator i = path.begin();
					i!=path.end(); i++) {
			int row, col;
			matrix->NodeToXY(*i, &row, &col);

			PyObject* tuple_element = PyTuple_New(2);
			PyTuple_SetItem(tuple_element,0, PyInt_FromLong(row));
			PyTuple_SetItem(tuple_element,1, PyInt_FromLong(col));
			
			PyList_SetItem(found_path, pos, tuple_element);	
			pos++;
		}
		PyTuple_SetItem(tuple_ret, 0, found_path);
		return tuple_ret;
	}

	protected:
	std::vector<void*> path;
	Matrix* matrix;

};

extern "C" {

static PyObject* 
Matrix_new(PyObject *dummy, PyObject *args) {

	PyObject* o;
	if (!PyArg_ParseTuple(args, "O", &o))
        	return NULL;

	Matrix* mat = new Matrix(o);
	return PyLong_FromSsize_t((ssize_t)mat);
}

static PyObject* 
Matrix_delete(PyObject *dummy, PyObject *args) {
	
	ssize_t mat_ptr;
	if (!PyArg_ParseTuple(args, "n", &mat_ptr))
        	return NULL;

	Matrix* m = (Matrix*)mat_ptr;	
	delete m;
	Py_INCREF(Py_None); 
	return Py_None;
}

static PyObject* 
Matrix_setMat(PyObject *dummy, PyObject *args) {
	
	PyObject* o;
	ssize_t mat_ptr;

	if (!PyArg_ParseTuple(args, "nO", &mat_ptr, &o))
        	return NULL;
	
	Matrix* mat = (Matrix*)mat_ptr;	
	mat->setMat(o);
	Py_INCREF(Py_None); 
	return Py_None;
}

static PyObject* 
AstarMatrix_new(PyObject *dummy, PyObject *args) {
	
	ssize_t mat_ptr;
	unsigned allocate;
	unsigned adj;

	if (!PyArg_ParseTuple(args, "nII", &mat_ptr, &allocate, &adj))
        	return NULL;
	
	Matrix* graph = (Matrix*)mat_ptr;	
	AstarMatrix* as_m = new AstarMatrix(graph, allocate, adj);

	return PyLong_FromSsize_t((ssize_t)as_m);
}

static PyObject* 
AstarMatrix_solve(PyObject *dummy, PyObject *args) {
	
	ssize_t astar_ptr;
	PyObject* start, *goal;

	if (!PyArg_ParseTuple(args, "nOO", &astar_ptr, &start, &goal))
        	return NULL;
	
	AstarMatrix* astar = (AstarMatrix*)astar_ptr;
	return astar->solve(start, goal);
}

static PyObject* 
AstarMatrix_reset(PyObject *dummy, PyObject *args) {

	ssize_t astar_ptr;
	if (!PyArg_ParseTuple(args, "n", &astar_ptr))
        	return NULL;
	
	AstarMatrix* astar = (AstarMatrix*)astar_ptr;
	astar->Reset();
	Py_INCREF(Py_None); 
	return Py_None;
}

static PyObject* 
AstarMatrix_delete(PyObject *dummy, PyObject *args) {
	
	ssize_t astar_ptr;
	if (!PyArg_ParseTuple(args, "n", &astar_ptr))
        	return NULL;

	AstarMatrix* astar = (AstarMatrix*)astar_ptr;	
	delete astar;
	Py_INCREF(Py_None); 
	return Py_None;
}

static PyMethodDef libastar_methods[] = {

    // "Python name", C Ffunction Code, Argument Flags, __doc__ description
    {"Matrix_new", Matrix_new, METH_VARARGS, "Don't use me!!"},
    {"Matrix_delete", Matrix_delete, METH_VARARGS, "Don't use me!!"},
    {"Matrix_setMat", Matrix_setMat, METH_VARARGS, "Don't use me!!"},
    {"AstarMatrix_new", AstarMatrix_new, METH_VARARGS, "Don't use me!!"},
    {"AstarMatrix_solve", AstarMatrix_solve, METH_VARARGS, "Don't use me!!"},
    {"AstarMatrix_reset", AstarMatrix_reset, METH_VARARGS, "Don't use me!!"},
    {"AstarMatrix_delete", AstarMatrix_delete, METH_VARARGS, "Don't use me!!"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initlibastar(void)
{
   (void)Py_InitModule("libastar", libastar_methods);
   import_array();
}


}

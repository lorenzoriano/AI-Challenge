#include <boost/python.hpp>
#include <numpy/arrayobject.h>
#include "micropather.h"
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/utility.hpp>
#include <exception>

using namespace micropather;
namespace bp = boost::python;

struct astar_value_exception: std::exception
{
    astar_value_exception(std::string str) {
	bp::handle<> h;
	msg = str;
    }

    const char* what() const throw() {
	return msg.c_str();
    }

    virtual ~astar_value_exception() throw() {

    }

    private:
	std::string msg;
};


class Matrix : public Graph {
	public:
	Matrix(PyObject* o) {
		mat_handle = bp::handle<PyObject>(o);
		mat = PyArray_FROMANY(mat_handle.get(), NPY_DOUBLE,2,2, NPY_CARRAY);
		if (mat == NULL)
			throw astar_value_exception("Wrong array!");
		cols = PyArray_DIM(mat, 1);
		rows = PyArray_DIM(mat, 0);
	}

	void setMat(PyObject* o) {
		mat_handle = bp::handle<PyObject>(o);
		mat = PyArray_FROMANY(mat_handle.get(), NPY_DOUBLE,2,2, NPY_CARRAY);
		if (mat == NULL)
			throw astar_value_exception("Wrong array!");
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
	
	int mat_cost(int r, int c) {
		while (r < 0)
			r = rows + r;
		while (r >= rows)
			r = r - rows;
		while (c < 0)
			c = cols + c;
		while (c >= cols)
			c = c - cols;
		PyArray_GETPTR2	(mat,r, c);
		return 1;
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

			int c = mat_cost( nx, ny );
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
	bp::handle<PyObject> mat_handle;
	PyObject* mat;
	int rows, cols;
};

class AstarMatrix : public MicroPather {
	public:
	AstarMatrix(Matrix *graph, unsigned allocate, unsigned typicalAdjacent) : 
		MicroPather(graph, allocate, typicalAdjacent) 
	{matrix = graph;}

	bp::tuple solve(bp::tuple start, bp::tuple goal) {
		int row1 = boost::python::extract<int>(start[0]);
		int col1 = boost::python::extract<int>(start[1]);
		int row2 = boost::python::extract<int>(goal[0]);
		int col2 = boost::python::extract<int>(goal[1]);

		void* start_state = matrix->XYToNode(row1, col1);
		void* end_state = matrix->XYToNode(row2, col2);

		float total_cost = 0;
		int res = MicroPather::Solve(start_state, 
					     end_state,
					     &path,
					     &total_cost);
	       	bp::list found_path;
		if (res == NO_SOLUTION)
			return bp::make_tuple(found_path, total_cost);	
		
		for (std::vector<void*>::iterator i = path.begin();
					i!=path.end(); i++) {
			int row, col;
			matrix->NodeToXY(*i, &row, &col);
			found_path.append(bp::make_tuple(row, col));
		}
		return bp::make_tuple(found_path, total_cost);
	}

	protected:
	Matrix* matrix;
	std::vector<void*> path;

};

BOOST_PYTHON_MODULE(libastar) {
	import_array();
	
	bp::class_<Matrix>("MatrixHolder", bp::init<PyObject*>())
	.def("setMat", &Matrix::setMat)
	;

	bp::class_<AstarMatrix, boost::noncopyable>("AstarMatrix", bp::init<Matrix*, unsigned, unsigned>())
	.def("solve", &AstarMatrix::solve)
	.def("reset", &AstarMatrix::Reset)
	;
}

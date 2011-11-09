#include <boost/python.hpp>
#include <arrayobject.h>
#include "micropather.h"
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <boost/python/suite/indexing/vector_indexing_suite.hpp>
#include <boost/utility.hpp>

using namespace micropather;
namespace bp = boost::python;


class Matrix : public Graph {
	public:
	Matrix(PyObject* o) {
		mat = PyArray_FROMANY(o, NPY_DOUBLE,1,1, NPY_CARRAY);
		cols = PyArray_DIM(mat, 1);
		rows = PyArray_DIM(mat, 0);
	}

	void setMat(PyObject* o) {
		mat = PyArray_FROMANY(o, NPY_DOUBLE,1,1, NPY_CARRAY);
		cols = PyArray_DIM(mat, 1);
		rows = PyArray_DIM(mat, 0);
	}

	void NodeToXY( void* node, int* row, int* col ) 
	{
		int index = (MP_UPTR)node;
		
		int r = index / cols;
		if (r < 0)
			r = rows + r;
		else if (r > rows)
			r = r - rows;
		int c = index - r * cols;
		if (c < 0)
			c = cols + c;
		else if (c > cols)
			c = c - cols;

		*row = r;
		*col = c;
	}

	void* XYToNode( int r, int c )
	{
		if (r < 0)
			r = rows + r;
		else if (r > rows)
			r = r - rows;
		if (c < 0)
			c = cols + c;
		else if (c > cols)
			c = c - cols;
		
		return (void*) ( r*cols+ c );
	}
	
	int mat_cost(int r, int c) {
		if (r < 0)
			r = rows + r;
		else if (r > rows)
			r = r - rows;
		if (c < 0)
			c = cols + c;
		else if (c > cols)
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
		const float cost[4] = { 1.0f, 1.0f, 1.0f, 1.0f};

		NodeToXY( node, &x, &y );

		for( int i=0; i<4; ++i ) {
			int nx = x + dx[i];
			int ny = y + dy[i];

			int c = mat_cost( nx, ny );
			if ( c > 0 ) {
				StateCost nodeCost = { XYToNode( nx, ny ), 
							cost[i] };
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

class Astar : public MicroPather {
	public:
	Astar(Matrix *graph, unsigned allocate, unsigned typicalAdjacent) : 
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
	
	bp::class_<Matrix>("AstarMatrix", bp::init<PyObject*>())
	.def("setMat", &Matrix::setMat)
	;

	bp::class_<Astar, boost::noncopyable>("Astar", bp::init<Matrix*, unsigned, unsigned>())
	.def("solve", &Astar::solve)
	.def("reset", &Astar::Reset)
	;
}

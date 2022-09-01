
# tutorial followed from https://github.com/IBMDecisionOptimization/docplex-examples/blob/master/examples/mp/jupyter/tutorials/Beyond_Linear_Programming.ipynb
# this script solves the transportation problem, wherein there are a set of supply nodes and a set of demand nodes in the network model.
# the goal is to minimize the cost of transportation (each arc in the model has a cost, similar to a weighted directed graph)
import inline as inline
import matplotlib
from docplex.mp.model import Model
import cplex
import matplotlib.pyplot as plt

# worth noting each of capacities, demands, and costs are dictionary objects in Python.  Store key-value pairs (similar to hashmap)

# set of 2-tuples, first element representing the supply node and the second element representing the capacity of said supply node
capacities = {1: 15, 2: 20}
# set of 2-tuples, first element representing demand node and 2nd element representing demand of said demand node
demands = {3: 7, 4: 10, 5: 15}
# set of 2-tuples, first element is itself a 2-tuple, first element representing origin node (supply node), 2nd element representing
# destination node (demand noe), and the 2nd element of the larger tuple representing the transportation cost between the source and
# destination node (i.e. the supply and demand node).
# essentially, this represents the directed weighted edge of the graph.
costs = {(1 ,3): 2, (1 ,5): 4, (2 ,4) :5, (2 ,5) :3}

source = range(1 ,3)  # supply nodes (source nodes), which are {1,2}
target = range(3 ,6)  # destination nodes (demand nodes), which are {3, 4, 5}

# create a model instance
transportationModel = Model(name = 'transportation')

# x(i,j) is flow going out of node i to node j (source to destination node, i.e. supply to demand node)
# directed graph, so x(i,j) does not necessarily equal x(j,i)
x = {(i, j): transportationModel.continuous_var(name = 'x_{0}_{1}'.format(i ,j)) for i in source for j in target}

# each arc (edge) has a cost (weight).  Minimize cost of flows while supplying demand of demand nodes.
transportationModel.minimize(transportationModel.sum(x[i ,j] * costs.get((i ,j), 0) for i in source for j in target))

transportationModel.print_information()
print("\n\n")

## SET UP THE CONSTRAINTS ##

# for each source (supply) node, the total outgoing flow must be <= available quality.
for i in source:
    transportationModel.add_constraint(transportationModel.sum(x[i ,j] for j in target) <= capacities[i])

# for each target (demand) node, the total outgoing flow must be >= demand.
for j in target:
    transportationModel.add_constraint(transportationModel.sum(x[i ,j] for i in source) >= demands[j])


transportationModel.minimize(transportationModel.sum(x[i, j] * costs.get((i ,j), 0)))

# objective is 0.000 in solution. not sure what that means exactly.
tms = transportationModel.solve()
assert tms
tms.display()
# x_1_5 = 15.000, means that from supply node 1 to demand node 5 we send 15 units.
# x_2_3 = 10.000 means that from supply node 1 to demand node 3, send 10 units. (??? 2 and 3 aren't connected in documentation?)
# x_2_4 = 10.000 means that from supply node 2 to demande node 4, send 10 units.


#piecewise and cplex

piecewiseModel = Model(name='piecewise with slopes')

# this is the graph of a piecewise function, computed using the slope on each interval.
# 'slope' in this example represents the cost of each unit being sold.  but it can represent anything, really.
# when [0, 1000] items are shipped, the slope is 0.4.
# when [1000, 3000] items are shipped, the slope is 0.2.
# when [3000, infinity) items are shipped, the slope is 0.1.
pwf1 = piecewiseModel.piecewise_as_slopes([(0 ,0), (0.4, 1000), (0.2, 3000)], lastslope=0.1)
# plot the function
pwf1.plot(lx=-1, rx=4000, k = 1, color= 'b', marker = 's', linewidth=2)

# this piecewise function is computed using 'break points' (it's the same as the above function, just calculated differently)
# break points are just xy-points of where the piecewise function changes.
# final slope is 0.1, which sets the slope from point (3000, 800) to infinity as 0.1
pwf2 = piecewiseModel.piecewise(preslope=0, breaksxy=[(0 ,0), (1000 ,400), (3000, 800)], postslope = 0.1)
pwf2.plot(lx = -1, rx = 4000, k = 1, color = 'r', marker = 'o', linewidth = 2)





#Integer Optimization
print("\n\n")
integerModel = Model(name = 'integer_programming')

#specific methods to make integer and binary variables in Docplex
# note that a binary variable is basically a boolean variable.
binaryVar = integerModel.binary_var(name='boolean_var')
integerVar = integerModel.integer_var(name='int_var')
integerModel.print_information()
print("\n\n")

#this is the integer programming problem from part 1, except
integerModel = Model(name='ip_telephone_production')

desk = integerModel.integer_var(name='desk')
cell = integerModel.integer_var(name='cell')

#add constraints for desk and cell phone production
integerModel.add_constraint(desk >=100)
integerModel.add_constraint(cell >= 100)

#constraint for assembly time limit
integerModel.add_constraint(0.2 * desk + 0.4 * cell <= 401)
#constraint for painting time limit
integerModel.add_constraint(0.5 * desk + 0.4 * cell <= 492)

si = integerModel.solve()
integerModel.print_solution()

## Set up decision variables

#Modeling yes/no decisions with binary variables
telephoneModel2 = Model('decision_phone')
#two variables per machine type
desk = telephoneModel2.integer_var(name='desk', lb=100) #lower bound of this variable is 100
cell = telephoneModel2.continuous_var(name='cell', lb=100)
#production on desk and cell phones for original machine
desk1 = telephoneModel2.integer_var(name='desk1')
cell1 = telephoneModel2.integer_var(name='cell1')
#production on desk and cell phones for new machine (manufactures cell phones faster in 15 mins, but desktop phones slower in 18 mins)
desk2 = telephoneModel2.integer_var(name='desk2')
cell2 = telephoneModel2.integer_var(name='cell2')

#boolean yes/no variable (aka binary variable)
z = telephoneModel2.binary_var(name='z')


## Set up constraints
telephoneModel2.add_constraint(desk == desk1 + desk2)
telephoneModel2.add_constraint(cell == cell1 + cell2)

#production on original assembly machine must be <=400 if the 'z' boolean variable is true
#this is the case when z = 1, as we get <= 400 * 1 <-> <=400.
telephoneModel2.add_constraint(0.2 * desk1 + 0.4 * cell1 <= 400 * z)

#production on new assembly machine must be <= 430 if the 'z' variable is false.
#1-z is 1 (true) if z is 0 (false). So this is basically saying "if !z, then..."
telephoneModel2.add_constraint(0.25 * desk2 + 0.3 * cell2 <= 430 * (1-z))

#painting machine limit: identical to original problem
telephoneModel2.add_constraint(0.5 * desk + 0.4 * cell <= 400)

# EXPRESSING THE OBJECTIVE:
# objective here is identical to original telephone problem: maximize total profit, using total productions.
telephoneModel2.maximize(12 * desk + 20 * cell)

#now, SOLVE the model:
telephoneModel2Solution = telephoneModel2.solve(log_output=True)
assert telephoneModel2
telephoneModel2.print_solution()
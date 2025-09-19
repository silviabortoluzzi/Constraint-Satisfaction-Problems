from typing import Any
from queue import Queue


class CSP:
    def __init__(
        self,
        variables: list[str],
        domains: dict[str, set],
        edges: list[tuple[str, str]],
    ):
        """Constructs a CSP instance with the given variables, domains and edges.
        
        Parameters
        ----------
        variables : list[str]
            The variables for the CSP
        domains : dict[str, set]
            The domains of the variables
        edges : list[tuple[str, str]]
            Pairs of variables that must not be assigned the same value
        """
        self.variables = variables
        self.domains = domains

    # Binary constraints as a dictionary mapping variable pairs to a set of value pairs.
    #
    # To check if variable1=value1, variable2=value2 is in violation of a binary constraint:
    # if (
    #     (variable1, variable2) in self.binary_constraints and
    #     (value1, value2) not in self.binary_constraints[(variable1, variable2)]
    # ) or (
    #     (variable2, variable1) in self.binary_constraints and
    #     (value1, value2) not in self.binary_constraints[(variable2, variable1)]
    # ):
    #     Violates a binary constraint
        self.binary_constraints: dict[tuple[str, str], set] = {}

        for variable1, variable2 in edges:
            # Original code: both (value1, value2) and (value2, value1) are stored under the same key (variable1, variable2), 
            # which mixes the two directions  
            # self.binary_constraints[(variable1, variable2)] = set()
            # for value1 in self.domains[variable1]:
            #     for value2 in self.domains[variable2]:
            #         if value1 != value2:
            #             self.binary_constraints[(variable1, variable2)].add((value1, value2))
            #             self.binary_constraints[(variable1, variable2)].add((value2, value1))

            # new code: (value1, value2) is stored under (variable1, variable2) and (value2, value1) under (variable2, variable1), 
            # so each direction is kept separate and AC-3 works correctly.
            if (variable1, variable2) not in self.binary_constraints:
                self.binary_constraints[(variable1, variable2)] = set()
            if (variable2, variable1) not in self.binary_constraints:
                self.binary_constraints[(variable2, variable1)] = set()

            for value1 in self.domains[variable1]:
                for value2 in self.domains[variable2]:
                    if value1 != value2:
                        self.binary_constraints[(variable1, variable2)].add((value1, value2))
                        self.binary_constraints[(variable2, variable1)].add((value2, value1))

    def ac_3(self) -> bool:
        """Performs AC-3 on the CSP.
        Meant to be run prior to calling backtracking_search() to reduce the search for some problems.
        
        Returns
        -------
        bool
            False if a domain becomes empty, otherwise True
        """ 
        queue = Queue()

        # Initialize the queue with all arcs in the CSP (both directions)
        for (Xi, Xj) in self.binary_constraints.keys():
            queue.put((Xi, Xj))
            queue.put((Xj, Xi))

        # Process arcs until the queue is empty
        while not queue.empty():
            (Xi, Xj) = queue.get()  # Take one arc from the queue

            if self.revise(Xi, Xj):
                if not self.domains[Xi]: # if size of Di = 0 then return false
                    return False
                for (Xk, Xl) in self.binary_constraints.keys():
                    if Xl == Xi and Xk != Xj:
                        queue.put((Xk, Xi)) # Put back into the queue the arcs that point to Xi

        return True

    def revise(self, Xi: str, Xj: str) -> bool:
        """Revise the domain of Xi to enforce arc consistency with Xj.

        Parameters
        ----------
        Xi : str
            The variable whose domain may be reduced.
        Xj : str
            The variable used to check consistency.

        Returns
        -------
        bool
            True if a value was removed from Xi s domain, False otherwise.
        """
        revised = False
        to_remove = set()

        # For each value x in the domain of Xi
        for x in self.domains[Xi]:
            # Check if there is at least one value y in Dj that is consistent
            if not any( # If there is no y that supports x, then x is an impossible value for Xi
                (x, y) in self.binary_constraints.get((Xi, Xj), set())
                for y in self.domains[Xj]
            ):
                # If no such y exists, mark x for removal later
                to_remove.add(x)
                revised = True

        # Remove unsupported values from Xi's domain
        for x in to_remove:
            self.domains[Xi].remove(x)

        return revised


    def backtracking_search(self) -> None | dict[str, Any]:
        """Performs backtracking search on the CSP.
        
        Returns
        -------
        None | dict[str, Any]
            A solution if any exists, otherwise None
        """
        self.backtrack_calls = 0 # To count every call to backtrack
        self.backtrack_failures = 0 # To count every time backtrack returns None (failure)

        def backtrack(assignment: dict[str, Any]):
            self.backtrack_calls += 1 # update call count
            if len(assignment) == len(self.variables): # If assignment is complete
                return assignment
            var = next(v for v in self.variables if v not in assignment) # Select the first unassigned variable (next() stops after finding the first)
            for value in self.domains[var]: # For each value in the variable's domain
                consistent = True
                #Check all binary constraints involving this variable
                for (var1, var2), allowed_pairs in self.binary_constraints.items(): 
                    if var == var1 and var2 in assignment and (value, assignment[var2]) not in allowed_pairs: # If var1 is the current variable and var2 is assigned, check if the pair is not allowed
                        consistent = False
                        break
                    if var == var2 and var1 in assignment and (assignment[var1], value) not in allowed_pairs: #same for the other direction
                        consistent = False
                        break

                if consistent:
                    assignment[var] = value # Assign value to variable
                    result = backtrack(assignment) # Recursively call backtrack with the new assignment
                    if result is not None:
                        return result # If the recursion returns a complete solution (meaning len(assignment) == len(self.variables) returns assignment), propagate it up so that the search ends here
                    del assignment[var] # if no complete solution was found remove the assignment (backtrack) 
            
            self.backtrack_failures += 1 # update failure count
            return None # If no value worked out, return None (failure)
       
        return backtrack({})


def alldiff(variables: list[str]) -> list[tuple[str, str]]:
    """Returns a list of edges interconnecting all of the input variables
    
    Parameters
    ----------
    variables : list[str]
        The variables that all must be different

    Returns
    -------
    list[tuple[str, str]]
        List of edges in the form (a, b)
    """
    return [(variables[i], variables[j]) for i in range(len(variables) - 1) for j in range(i + 1, len(variables))]

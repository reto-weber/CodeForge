class
	CALCULATOR

create
	make

feature
	make
			-- Simple calculator demonstration
		do
			a := 10
			b := 5
		end
feature {NONE}
    a, b: INTEGER
    add: INTEGER
        do
            Result := a + b
        ensure
            Result = a + b
        end
    
    subtract: INTEGER
        do
            Result := a - b
        ensure
            Result = a - b
        end
    
    multiply: INTEGER
        do
            Result := a * b
        ensure
            Result = a * b
        end
    
    divide: INTEGER
        do
            Result := a // b
        ensure
            Result = a // b
        end

end

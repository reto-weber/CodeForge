class
	CALCULATOR

create
	make

feature
	make
			-- Simple calculator demonstration
		local
			a, b: INTEGER
			result: INTEGER
		do
			a := 10
			b := 5
			
			print ("Simple Calculator Demo%N")
			print ("=====================%N")
			
			-- Addition
			result := a + b
			print ("Addition: " + a.out + " + " + b.out + " = " + result.out + "%N")
			
			-- Subtraction
			result := a - b
			print ("Subtraction: " + a.out + " - " + b.out + " = " + result.out + "%N")
			
			-- Multiplication
			result := a * b
			print ("Multiplication: " + a.out + " * " + b.out + " = " + result.out + "%N")
			
			-- Division
			if b /= 0 then
				result := a // b
				print ("Division: " + a.out + " // " + b.out + " = " + result.out + "%N")
			end
		end

end

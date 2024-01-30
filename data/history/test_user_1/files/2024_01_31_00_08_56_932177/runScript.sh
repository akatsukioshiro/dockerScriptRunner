#!/bin/bash

# List of Python files to run in sequence
shell_commands=(

)

# Loop through the list and run each Python file
for scmd in "${shell_commands[@]}"; do
    echo "Running $scmd..."
    
    # Run the Python file and capture its output
    output=$($scmd 2>&1)
    
    # Display the output
    echo "Output for $scmd:"
    echo "$output"
    
    # Add a separator line
    echo "\n----------------------------------------\n"
done
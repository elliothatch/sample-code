using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Amil
{
    public class VirtualMachine
    {
        public int totalMemory;
        public int remainingMemory;
        public int programCounter;
        public List<Instruction> instructions;
        public Dictionary<string, Value> variables;
        public Stack<Value> stack;

        public VirtualMachine(int totalMemory)
        {
            this.totalMemory = totalMemory;
            remainingMemory = totalMemory;
            variables = new Dictionary<string, Value>();
            programCounter = 0;
            stack = new Stack<Value>();
        }

        public void LoadInstructions(List<Instruction> instructions)
        {
            this.instructions = instructions;
        }

        public void Execute()
        {
            while(programCounter < instructions.Count)
            {
                Step();
            }
        }

        public void Step()
        {
            Instruction instruction = instructions[programCounter];
            switch(instruction.iType)
            {
                case InstructionType.DECLARATION:
                    variables.Add((instruction as DeclarationInstruction).name, new NoneValue());
                    remainingMemory -= 4; //TODO: add types with memory usage
                    break;
                case InstructionType.PRINT:
                    Console.WriteLine(stack.Pop().print());
                    break;
                case InstructionType.PUSH_CONST:
                    stack.Push((instruction as PushConstInstruction).value);
                    break;
                case InstructionType.LOAD:
                    string varName = (instruction as LoadInstruction).name;
                    if(!variables.ContainsKey(varName))
                    {
                        throw new Exception(string.Format("Tried to use undeclared variable '{}'", varName));
                    }
                    stack.Push(variables[varName]);
                    break;
                case InstructionType.ADD:
                case InstructionType.SUBTRACT:
                case InstructionType.MULTIPLY:
                case InstructionType.DIVIDE:
                    Value rhs = stack.Pop();
                    Value lhs = stack.Pop();
                    stack.Push(computeNumericalOperation(lhs, rhs, instruction.iType));
                    break;
                case InstructionType.POP:
                    stack.Pop();
                    break;
                case InstructionType.BRANCH:
                    Value condition = stack.Pop();
                    if(!(condition is BooleanValue)) {
                        throw new Exception(string.Format("{}: BRANCH condition must have type boolean", programCounter));
                    }

                    if(!(condition as BooleanValue).b)
                    {
                        //jump past body
                        programCounter += (instruction as BranchInstruction).jumpCount;
                    }
                    break;
                default:
                    throw new Exception(string.Format("{}: Unknown instruction {}", programCounter, instruction.iType));
            }
            programCounter++;
        }

        Value computeNumericalOperation(Value lhs, Value rhs, InstructionType iType)
        {
            if(!(lhs is IntegerValue) || !(rhs is IntegerValue))
            {
                throw new Exception(string.Format("{}: Cannot apply numerical operation {} to values of type {} and {}", programCounter, iType, lhs.vType, rhs.vType));
            }

            switch(iType)
            {
                case InstructionType.ADD:
                    return new IntegerValue((lhs as IntegerValue).n + (rhs as IntegerValue).n);
                case InstructionType.SUBTRACT:
                    return new IntegerValue((lhs as IntegerValue).n - (rhs as IntegerValue).n);
                case InstructionType.MULTIPLY:
                    return new IntegerValue((lhs as IntegerValue).n * (rhs as IntegerValue).n);
                case InstructionType.DIVIDE:
                    return new IntegerValue((lhs as IntegerValue).n / (rhs as IntegerValue).n);
                default:
                    throw new Exception(string.Format("{}: Unknown numerical operation {}", programCounter, iType));
            }
        }
    }

    public enum InstructionType
    {
        DECLARATION,
        PRINT,
        PUSH_CONST,
        LOAD,
        ADD,
        SUBTRACT,
        MULTIPLY,
        DIVIDE,
        POP,
        BRANCH
    }

    public abstract class Instruction
    {
        public readonly InstructionType iType;
        public Instruction(InstructionType iType)
        {
            this.iType = iType;
        }
    }

    public class DeclarationInstruction : Instruction
    {
        public readonly string name;
        public DeclarationInstruction(string name)
            : base(InstructionType.DECLARATION)
        {
            this.name = name;
        }
    }

    public class PrintInstruction : Instruction
    {
        public PrintInstruction()
            : base(InstructionType.PRINT)
        {
        }
    }

    public class PushConstInstruction : Instruction
    {
        public Value value;
        public PushConstInstruction(Value value)
            : base(InstructionType.PUSH_CONST)
        {
            this.value = value;
        }
    }

    public class LoadInstruction : Instruction
    {
        public string name;
        public LoadInstruction(string name)
            : base(InstructionType.LOAD)
        {
            this.name = name;
        }
    }
    public class AddInstruction : Instruction
    {
        public AddInstruction()
            : base(InstructionType.ADD)
        {
        }
    }
    public class SubtractInstruction : Instruction
    {
        public SubtractInstruction()
            : base(InstructionType.SUBTRACT)
        {
        }
    }
    public class MultiplyInstruction : Instruction
    {
        public MultiplyInstruction()
            : base(InstructionType.MULTIPLY)
        {
        }
    }
    public class DivideInstruction : Instruction
    {
        public DivideInstruction()
            : base(InstructionType.DIVIDE)
        {
        }
    }

    public class PopInstruction : Instruction
    {
        public PopInstruction()
            : base(InstructionType.POP)
        {
        }
    }

    public class BranchInstruction : Instruction
    {
        // if the stack top evaluates to false, skip jumpCount instructions
        public int jumpCount;
        public BranchInstruction(int jumpCount)
            : base(InstructionType.BRANCH)
        {
            this.jumpCount = jumpCount;
        }
    }
}

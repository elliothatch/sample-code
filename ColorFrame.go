//https://github.com/elliothatch/Insurgency/blob/master/Insurgency/EntityComponent.h
package neopixeldisplay

import(
	"fmt"
	"errors"
)

/********** Color **********/
type Color uint32

func (color Color) GetRed() uint32 {
	return uint32(color & (1<<8 - 1))
}

func (color Color) GetGreen() uint32 {
	return uint32((color >> 16) & (1<<8 - 1))
}

func (color Color) GetBlue() uint32 {
	return uint32((color >> 8) & (1<<8 - 1))
}

//func (color Color) GetWhite() uint32 {
	//return uint32((color >> 24) & (2<<8 - 1))
//}

func MakeColor(red, green, blue uint32) Color {
	return Color((green << 16) | (blue << 8) | red)
}

func (c Color) Add(c2 Color) Color {
	return MakeColor(
		MinUint32(255, c.GetRed() + c2.GetRed()),
		MinUint32(255, c.GetGreen() + c2.GetGreen()),
		MinUint32(255, c.GetBlue() + c2.GetBlue()))
}

func MinUint32(a, b uint32) uint32 {
	if a < b {
		return a
	} else {
		return b
	}
}

/********** ColorFrame **********/

type ColorOverflowMode int
const(
	Error ColorOverflowMode = iota
	Clip
	Wrap
)

//all "high level" drawing types should take a target ColorFrame and call its Draw() function after setting the frame
//any "high level" drawing type that can be directly set pixel by pixel (e.g. a layer in a LayerView) should be a DisplayView. The DisplayView should create a ColorFrame, set the frame's parent
//to itself, and return a pointer to that ColorFrame that can be modified. Users who modify the frame must call Draw() which calls the parent's Draw()
//Additionally, ColorFrame itself is a DisplayView and many DisplayViews return
type DisplayView interface  {
	Draw()
}


type ColorFrame struct {
	Width, Height int
	colors [][]Color
	parent DisplayView
}

func MakeColorFrame(width, height int, color Color) ColorFrame {
	colors := make([][]Color, height)
	for i := 0; i < height; i++ {
		colors[i] = make([]Color, width)
	}

	for i := 0; i < height; i++ {
		for j := 0; j < width; j++ {
			colors[i][j] = color
		}
	}

	return ColorFrame{width, height, colors, nil}
}

//returns x, y, errorCode, error
func (c ColorFrame) calcOverflowPosition(x, y int, overflowMode ColorOverflowMode) (int, int, int, error) {
	if y < 0 || x < 0 || y >= len(c.colors) || x >= len(c.colors[y]) {
		switch overflowMode {
			case Error:
				width := "?"
				if y >= 0 && y < len(c.colors) {
					width = fmt.Sprintf("%v", len(c.colors))
				}
				return 0, 0, 1, errors.New(fmt.Sprintf("ColorFrame.Set: tried to set (%v,%v) but the frame has dimensions (%v,%v)",
					x, y, width, len(c.colors)))
			case Clip:
				return 0, 0, 2, nil
			case Wrap:
				return x % len(c.colors[y]), y % len(c.colors), 0, nil
		}
	}
	return x, y, 0, nil
}

//returns 0,0,0 if set to clip mode
func (c ColorFrame) Get(x, y int, overflowMode ColorOverflowMode) Color {
	x, y, errorCode, err := c.calcOverflowPosition(x, y, overflowMode)
	if errorCode == 1 {
		panic(err)
	} else if errorCode == 2 {
		return MakeColor(0,0,0)
	}

	return c.colors[y][x]
}
func (c ColorFrame) Set(x, y int, color Color, overflowMode ColorOverflowMode) {
	x, y, errorCode, err := c.calcOverflowPosition(x, y, overflowMode)
	if errorCode == 1 {
		panic(err)
	} else if errorCode == 2 {
		// do nothing
		return
	}

	c.colors[y][x] = color
}

func (c ColorFrame) SetAll(color Color) {
	for i := 0; i < len(c.colors); i++ {
		for j := 0; j < len(c.colors[i]); j++ {
			c.colors[i][j] = color
		}
	}
}

func (c ColorFrame) SetRect(x, y int, source ColorFrame, overflowMode ColorOverflowMode) {
	for i := 0; i < len(source.colors); i++ {
		for j := 0; j < len(source.colors[i]); j++ {
			c.Set(x+j, y+i, source.colors[i][j], overflowMode)
		}
	}
}

func (c ColorFrame) Draw() {
	if c.parent != nil {
		c.parent.Draw()
	}
}

type ColorCombineMode int

func (c ColorFrame) CombineRect(x, y int, source ColorFrame, combineMode ColorCombineMode, overflowMode ColorOverflowMode) {
	for i := 0; i < source.Height; i++ {
		for j := 0; j < source.Width; j++ {
			color := source.Get(j,i, overflowMode)
			switch combineMode {
			case OverwriteAll:
				c.Set(x+j, y+i, color, overflowMode)
			case Overwrite:
				if color != MakeColor(0,0,0) {
					c.Set(x+j, y+i, color, overflowMode)
				}
			case Add:
				c.Set(x+j, y+i, c.Get(x+j, y+i, overflowMode).Add(color), overflowMode)
			case SetWhite:
				if color != MakeColor(0,0,0) {
					if c.Get(x+j, y+i, overflowMode) != MakeColor(0,0,0) {
						c.Set(x+j, y+i, MakeColor(255,255,255), overflowMode)
					} else {
						c.Set(x+j, y+i, color, overflowMode)
					}
				}
			}
		}
	}
}

const(
	OverwriteAll ColorCombineMode = iota
	Overwrite // 0s don't overwrite colors
	Add
	SetWhite

)


/********** Color Helper Constructors **********/
func MakeColorHue(hue uint32) Color {
	for hue < 0 {
		hue += 255
	}
	for hue > 255 {
		hue -= 255
	}
	if hue < 85 {
		return MakeColor(hue*3, 255-hue*3, 0)
	} else if hue < 170 {
		hue -= 85
		return MakeColor(255-hue*3, 0, hue*3)
	} else {
		hue -= 170
		return MakeColor(0, hue*3, 255-hue*3)
	}
}

func MakeColorNumberChar2x3(num int, fgColor, bgColor Color) ColorFrame {
	colors := MakeColorFrame(2, 3, bgColor)
	for x := 0; x < colors.Width; x++ {
		for y := 0; y < colors.Height; y++ {
			if NumberCharTemplates[num][y][x] {
				colors.Set(x, y, fgColor, Error)
			}
		}
	}

	return colors
}

var NumberCharTemplates [][][]bool = [][][]bool{
	//0
	[][]bool{
		[]bool{true, true},
		[]bool{true, true},
		[]bool{true, true},
	},
	//1
	[][]bool{
		[]bool{false, true},
		[]bool{false, true},
		[]bool{false, true},
	},
	//2
	[][]bool{
		[]bool{true, true},
		[]bool{false, true},
		[]bool{true, false},
	},
	//3
	[][]bool{
		[]bool{true, true},
		[]bool{false, true},
		[]bool{true, true},
	},
	//4
	[][]bool{
		[]bool{true, false},
		[]bool{true, true},
		[]bool{false, true},
	},
	//5
	[][]bool{
		[]bool{true, true},
		[]bool{true, false},
		[]bool{false, true},
	},
	//6
	[][]bool{
		[]bool{true, false},
		[]bool{true, true},
		[]bool{true, true},
	},
	//7
	[][]bool{
		[]bool{true, true},
		[]bool{false, true},
		[]bool{true, false},
	},
	//8
	[][]bool{
		[]bool{true, true},
		[]bool{false, false},
		[]bool{true, true},
	},
	//9
	[][]bool{
		[]bool{true, true},
		[]bool{true, true},
		[]bool{false, true},
	},
}

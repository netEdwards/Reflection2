import React from "react";

type ButtonVariant = "primary" | "secondary" 
type ButtonSize = "sm" | "md" | "lg"
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
};
const baseStyle: React.CSSProperties = {
    border: "",
    borderRadius: "",
}

const variants: Record<ButtonVariant, React.CSSProperties> = {
    primary: {
        background: "",
        color: "",
    },
    secondary: {
        background: "",
        color: "",
    },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
    sm: {padding: "", fontSize: ""},
    md: {padding: "", fontSize: ""},
    lg: {padding: "", fontSize: ""},
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  style,
  children,
  ...rest
}) => {
    const combinedStyles: React.CSSProperties = {
        ...baseStyle,
        ...variants,
        ...sizeStyles,
        ...style, //overrides...
    }
    return (
        <button
            style={combinedStyles}
            onMouseDown={(e)=>{
                (e.currentTarget as HTMLButtonElement).style.transform = "translateY(1px)";
            }}
            onMouseUp={(e) => {
                (e.currentTarget as HTMLButtonElement).style.transform = "translateY(0)";
            }}
            {...rest}
        >
            {children}
        </button>
    );
};
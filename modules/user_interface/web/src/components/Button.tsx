import React from "react";

type ButtonVariant = "primary" | "secondary" 
type ButtonSize = "sm" | "md" | "lg"
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: ButtonVariant;
    size?: ButtonSize;
};
const baseStyle: React.CSSProperties = {
    border: "none",
    borderRadius: "10px",
    fontFamily: "inherit",
    fontWeight: 600,
    cursor: "pointer",
    color: "white",
}

const variants: Record<ButtonVariant, React.CSSProperties> = {
    primary: {
        background: "rgb(90, 100, 200)",
    },
    secondary: {
        background: "rgb(45, 45, 45)",
    },
};

const sizeStyles: Record<ButtonSize, React.CSSProperties> = {
    sm: { padding: "0.45rem 0.9rem", fontSize: "0.85rem" },
    md: { padding: "0.7rem 1.4rem", fontSize: "1rem" },
    lg: { padding: "0.9rem 1.8rem", fontSize: "1.1rem" },
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
        ...variants[variant],
        ...sizeStyles[size],
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
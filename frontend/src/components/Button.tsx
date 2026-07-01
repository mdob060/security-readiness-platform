import React from "react";

type Variant = "primary" | "secondary" | "danger" | "success" | "ghost";

const variantClasses: Record<Variant, string> = {
  primary: "bg-blue-600 hover:bg-blue-500 text-white border-transparent",
  secondary:
    "bg-[#11161d] hover:bg-[#171d26] text-slate-200 border-[#1e2530]",
  danger: "bg-red-600/90 hover:bg-red-600 text-white border-transparent",
  success: "bg-green-600/90 hover:bg-green-600 text-white border-transparent",
  ghost: "bg-transparent hover:bg-[#11161d] text-slate-400 border-transparent",
};

export function Button({
  children,
  variant = "primary",
  className = "",
  disabled,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      disabled={disabled}
      className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${variantClasses[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`w-full rounded-md border border-[#1e2530] bg-[#11161d] px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-blue-500 focus:outline-none ${
        props.className || ""
      }`}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={`w-full rounded-md border border-[#1e2530] bg-[#11161d] px-3 py-1.5 text-sm text-slate-200 focus:border-blue-500 focus:outline-none ${
        props.className || ""
      }`}
    />
  );
}

export function Textarea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement>
) {
  return (
    <textarea
      {...props}
      className={`w-full rounded-md border border-[#1e2530] bg-[#11161d] px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-blue-500 focus:outline-none ${
        props.className || ""
      }`}
    />
  );
}

export function Label({ children }: { children: React.ReactNode }) {
  return (
    <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">
      {children}
    </label>
  );
}

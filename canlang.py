#!/usr/bin/env python3
"""
CAN Language Interpreter  v2.0
================================
A complete interpreter for the CAN programming language.

Types:
  yap    → boolean  (fr = true, cap = false)
  etco   → number   (int or float)
  Ower   → string
  nada   → null / None
  rack   → array    (dynamic typed list)

Keywords:
  spill(...)                         → print (no newline: spillRaw)
  think TYPE name = expr             → variable declaration
  no cap (cond) { }                  → if
  lowkey (cond) { }                  → else if
  bet { }                            → else
  ghost (cond) { }                   → while loop
  grind { } ghost (cond);            → do-while loop
  slide (init; cond; step) { }       → for loop
  foreach (item in arr) { }          → for-each loop
  vibe TYPE name(params) { }         → function declaration
  bounce expr                        → return
  drop                               → break
  skip                               → continue
  catch("prompt")                    → input as string
  catchNum("prompt")                 → input as number
  yeet expr;                         → throw / raise error
  shield { } miss (Ower e) { }       → try / catch error
  rack name = [a, b, c];             → array literal
  name[i]                            → array indexing (read)
  name[i] = expr;                    → array index assignment
  vibe TYPE name(TYPE* params)      → variadic function

Operators:
  +  -  *  /  %  **                  → arithmetic (** = power)
  ==  !=  <  >  <=  >=               → comparison
  &&  ||  !                          → logical
  =  +=  -=  *=  /=  %=  **=        → assignment

Comments:
  ^ single line comment
  ... multi line comment ...
"""
from __future__ import annotations
import sys, math, random, time, os

# ═══════════════════════════════════════════════════════════════
#  LEXER
# ═══════════════════════════════════════════════════════════════

class LexerError(Exception): pass

class Token:
    __slots__ = ("type", "value", "line", "col")
    def __init__(self, type_: str, value, line: int, col: int):
        self.type  = type_
        self.value = value
        self.line  = line
        self.col   = col
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.col})"

class Lexer:
    KEYWORDS = {
        "spill", "spillRaw", "think",
        "yap", "etco", "Ower", "nada", "rack",
        "fr", "cap",
        "no", "lowkey", "bet",
        "ghost", "grind",
        "slide", "foreach", "in",
        "vibe", "bounce",
        "drop", "skip",
        "catch", "catchNum",
        "yeet", "shield", "miss",
    }

    def __init__(self, text: str):
        self.text = text
        self.pos  = 0
        self.line = 1
        self.col  = 1

    def _peek(self, k: int = 0) -> str:
        idx = self.pos + k
        return self.text[idx] if idx < len(self.text) else "\0"

    def _advance(self) -> str:
        ch = self._peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_ws_and_comments(self):
        while True:
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == "^":
                while self._peek() not in ("\n", "\0"):
                    self._advance()
                continue
            if ch == "." and self._peek(1) == "." and self._peek(2) == ".":
                self._advance(); self._advance(); self._advance()
                while not (self._peek() == "." and self._peek(1) == "." and self._peek(2) == "."):
                    if self._peek() == "\0":
                        raise LexerError(f"Unterminated multi-line comment at {self.line}:{self.col}")
                    self._advance()
                self._advance(); self._advance(); self._advance()
                continue
            break

    def tokenize(self) -> list:
        tokens = []
        while True:
            self._skip_ws_and_comments()
            ch = self._peek()
            if ch == "\0":
                break
            sl, sc = self.line, self.col

            # Identifier / keyword
            if ch.isalpha() or ch == "_":
                ident = ""
                while self._peek().isalnum() or self._peek() == "_":
                    ident += self._advance()
                if ident in self.KEYWORDS:
                    tokens.append(Token(ident.upper(), ident, sl, sc))
                else:
                    tokens.append(Token("IDENT", ident, sl, sc))
                continue

            # Number
            if ch.isdigit():
                num = ""
                has_dot = False
                while self._peek().isdigit() or (self._peek() == "." and not has_dot and self._peek(1).isdigit()):
                    if self._peek() == ".":
                        has_dot = True
                    num += self._advance()
                tokens.append(Token("NUMBER", num, sl, sc))
                continue

            # String literal
            if ch == '"':
                self._advance()
                s = ""
                while self._peek() != '"' and self._peek() != "\0":
                    if self._peek() == "\\":
                        self._advance()
                        esc = self._peek()
                        s += {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "r": "\r"}.get(esc, "\\" + esc)
                        self._advance()
                    else:
                        s += self._advance()
                if self._peek() != '"':
                    raise LexerError(f"Unterminated string at {self.line}:{self.col}")
                self._advance()
                tokens.append(Token("STRING", s, sl, sc))
                continue

            # Three-char operators
            three = ch + self._peek(1) + self._peek(2)
            if three in ("**=",):
                tokens.append(Token(three, three, sl, sc))
                self._advance(); self._advance(); self._advance()
                continue

            # Two-char operators
            two = ch + self._peek(1)
            if two in ("==", "!=", "<=", ">=", "&&", "||", "+=", "-=", "*=", "/=", "%=", "**", ".."):
                tokens.append(Token(two, two, sl, sc))
                self._advance(); self._advance()
                continue

            # Single-char tokens
            if ch in "(){};=,+-*/%<>![].:":
                tokens.append(Token(ch, ch, sl, sc))
                self._advance()
                continue

            raise LexerError(f"Unexpected character '{ch}' at {self.line}:{self.col}")

        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens


# ═══════════════════════════════════════════════════════════════
#  AST NODES
# ═══════════════════════════════════════════════════════════════

class AST: pass

class Program(AST):
    def __init__(self, stmts):          self.stmts = stmts

class Block(AST):
    def __init__(self, stmts):          self.stmts = stmts

class Spill(AST):
    def __init__(self, exprs, newline=True):
        self.exprs   = exprs
        self.newline = newline

class VarDecl(AST):
    def __init__(self, dtype, name, value):
        self.dtype, self.name, self.value = dtype, name, value

class Assign(AST):
    def __init__(self, name, op, value, index=None):
        self.name, self.op, self.value, self.index = name, op, value, index

class IfStmt(AST):
    def __init__(self, branches, else_block):
        self.branches   = branches
        self.else_block = else_block

class WhileStmt(AST):
    def __init__(self, cond, body):     self.cond, self.body = cond, body

class DoWhileStmt(AST):
    def __init__(self, body, cond):     self.body, self.cond = body, cond

class ForStmt(AST):
    def __init__(self, init, cond, step, body):
        self.init, self.cond, self.step, self.body = init, cond, step, body

class ForEachStmt(AST):
    def __init__(self, var, iterable, body):
        self.var, self.iterable, self.body = var, iterable, body

class FuncDecl(AST):
    def __init__(self, ret_type, name, params, body, variadic=False):
        self.ret_type = ret_type
        self.name     = name
        self.params   = params
        self.body     = body
        self.variadic = variadic

class ReturnStmt(AST):
    def __init__(self, value):          self.value = value

class BreakStmt(AST):    pass
class ContinueStmt(AST): pass

class YeetStmt(AST):
    def __init__(self, value):          self.value = value

class ShieldStmt(AST):
    def __init__(self, body, err_name, catch_body):
        self.body       = body
        self.err_name   = err_name
        self.catch_body = catch_body

class ExprStmt(AST):
    def __init__(self, expr):           self.expr = expr

class Literal(AST):
    def __init__(self, value):          self.value = value

class NullLiteral(AST): pass

class ArrayLiteral(AST):
    def __init__(self, elements):       self.elements = elements

class Var(AST):
    def __init__(self, name):           self.name = name

class IndexGet(AST):
    def __init__(self, obj, index):     self.obj, self.index = obj, index

class BinOp(AST):
    def __init__(self, op, left, right): self.op, self.left, self.right = op, left, right

class UnaryOp(AST):
    def __init__(self, op, operand):    self.op, self.operand = op, operand

class Call(AST):
    def __init__(self, name, args):     self.name, self.args = name, args

class MethodCall(AST):
    def __init__(self, obj, method, args):
        self.obj, self.method, self.args = obj, method, args

class CatchExpr(AST):
    def __init__(self, prompt):         self.prompt = prompt

class CatchNumExpr(AST):
    def __init__(self, prompt):         self.prompt = prompt

class TernaryExpr(AST):
    def __init__(self, cond, then_expr, else_expr):
        self.cond, self.then_expr, self.else_expr = cond, then_expr, else_expr


# ═══════════════════════════════════════════════════════════════
#  PARSER
# ═══════════════════════════════════════════════════════════════

class ParserError(Exception): pass

_EOF_TOK = Token("EOF", "", -1, -1)

class Parser:
    TYPE_TOKENS = {"YAP", "ETCO", "OWER", "NADA", "RACK"}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def _peek(self, k=0):
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else _EOF_TOK

    def _advance(self):
        tok = self._peek()
        self.pos += 1
        return tok

    def _expect(self, type_):
        tok = self._advance()
        if tok.type != type_:
            raise ParserError(
                f"Expected '{type_}' but got '{tok.type}' ({tok.value!r}) at {tok.line}:{tok.col}"
            )
        return tok

    def _match(self, *types):
        return self._peek().type in types

    def _parse_type(self):
        tok = self._advance()
        if tok.type not in self.TYPE_TOKENS:
            raise ParserError(
                f"Expected a type (yap/etco/Ower/nada/rack) but got '{tok.value}' at {tok.line}:{tok.col}"
            )
        return tok.value

    def parse(self):
        stmts = []
        while not self._match("EOF"):
            stmts.append(self._statement())
        return Program(stmts)

    def _block(self):
        self._expect("{")
        stmts = []
        while not self._match("}") and not self._match("EOF"):
            stmts.append(self._statement())
        self._expect("}")
        return Block(stmts)

    def _statement(self):
        tok = self._peek()

        if tok.type == "SPILL":    return self._spill_stmt(newline=True)
        if tok.type == "SPILLRAW": return self._spill_stmt(newline=False)
        if tok.type == "THINK":    return self._var_decl()
        if tok.type == "NO":       return self._if_stmt()
        if tok.type == "GHOST":    return self._while_stmt()
        if tok.type == "GRIND":    return self._do_while_stmt()
        if tok.type == "SLIDE":    return self._for_stmt()
        if tok.type == "FOREACH":  return self._foreach_stmt()
        if tok.type == "VIBE":     return self._func_decl()
        if tok.type == "BOUNCE":   return self._return_stmt()
        if tok.type == "YEET":     return self._yeet_stmt()
        if tok.type == "SHIELD":   return self._shield_stmt()
        if tok.type == "RACK":     return self._rack_decl()
        if tok.type == "DROP":
            self._advance(); self._expect(";"); return BreakStmt()
        if tok.type == "SKIP":
            self._advance(); self._expect(";"); return ContinueStmt()

        if tok.type == "IDENT":
            # Check for array index assignment: name[expr] = ...
            if self._peek(1).type == "[":
                return self._index_assign_or_expr()
            next_tok = self._peek(1)
            if next_tok.type in ("=", "+=", "-=", "*=", "/=", "%=", "**="):
                return self._assign_stmt()
            return self._expr_stmt()

        if tok.type in ("CATCH", "CATCHNUM"):
            return self._expr_stmt()

        raise ParserError(f"Unexpected token '{tok.value}' at {tok.line}:{tok.col}")

    def _spill_stmt(self, newline=True):
        self._advance()
        self._expect("(")
        exprs = []
        if not self._match(")"):
            exprs.append(self._expr())
            while self._match(","):
                self._advance()
                exprs.append(self._expr())
        self._expect(")")
        self._expect(";")
        return Spill(exprs, newline)

    def _rack_decl(self):
        """think rack name = [...]; or rack name = [...]; (bare rack)"""
        self._advance()  # consume 'rack'
        name = self._expect("IDENT").value
        self._expect("=")
        val  = self._expr()
        self._expect(";")
        return VarDecl("rack", name, val)

    def _var_decl(self):
        self._advance()  # consume 'think'
        # Support 'think rack name = [...]'
        dtype = self._parse_type()
        name  = self._expect("IDENT").value
        self._expect("=")
        val   = self._expr()
        self._expect(";")
        return VarDecl(dtype, name, val)

    def _assign_stmt(self):
        name    = self._advance().value
        op_tok  = self._advance()
        val     = self._expr()
        self._expect(";")
        op = op_tok.value
        # Strip trailing '=' for compound ops: '+=' -> '+', '**=' -> '**'
        pure_op = op[:-1] if op != "=" else ""
        return Assign(name, pure_op, val)

    def _index_assign_or_expr(self):
        """Handles: name[expr] = expr; or name[expr] as expression statement"""
        name = self._advance().value   # IDENT
        self._expect("[")
        idx = self._expr()
        self._expect("]")
        if self._match("="):
            self._advance()
            val = self._expr()
            self._expect(";")
            return Assign(name, "", val, index=idx)
        # It's actually an expression statement starting with indexing
        # Rebuild as expr stmt
        obj = IndexGet(Var(name), idx)
        # Continue parsing as possible method call / binary op
        # We need to re-enter expression parsing from this point
        # Simplest: build the node and hand to _expr_stmt_from
        # But we already consumed tokens — handle by wrapping
        # Check for method call on the result
        while self._match("."):
            self._advance()
            method = self._expect("IDENT").value
            self._expect("(")
            args = []
            if not self._match(")"):
                args.append(self._expr())
                while self._match(","):
                    self._advance()
                    args.append(self._expr())
            self._expect(")")
            obj = MethodCall(obj, method, args)
        self._expect(";")
        return ExprStmt(obj)

    def _if_stmt(self):
        self._expect("NO")
        self._expect("CAP")
        self._expect("(")
        cond = self._expr()
        self._expect(")")
        body = self._block()
        branches = [(cond, body)]

        while self._match("LOWKEY"):
            self._advance()
            self._expect("(")
            c = self._expr()
            self._expect(")")
            b = self._block()
            branches.append((c, b))

        else_block = None
        if self._match("BET"):
            self._advance()
            else_block = self._block()

        return IfStmt(branches, else_block)

    def _while_stmt(self):
        self._advance()
        self._expect("(")
        cond = self._expr()
        self._expect(")")
        body = self._block()
        return WhileStmt(cond, body)

    def _do_while_stmt(self):
        self._advance()  # consume 'grind'
        body = self._block()
        self._expect("GHOST")
        self._expect("(")
        cond = self._expr()
        self._expect(")")
        self._expect(";")
        return DoWhileStmt(body, cond)

    def _for_stmt(self):
        self._advance()
        self._expect("(")

        init_name = self._expect("IDENT").value
        init_op   = self._advance()
        if init_op.type not in ("=", "+=", "-=", "*=", "/=", "%=", "**="):
            raise ParserError(f"Expected assignment in slide-init at {init_op.line}:{init_op.col}")
        init_val  = self._expr()
        pure      = init_op.value[:-1] if init_op.value != "=" else ""
        init      = Assign(init_name, pure, init_val)
        self._expect(";")

        cond = self._expr()
        self._expect(";")

        step_name = self._expect("IDENT").value
        step_op   = self._advance()
        if step_op.type not in ("=", "+=", "-=", "*=", "/=", "%=", "**="):
            raise ParserError(f"Expected assignment in slide-step at {step_op.line}:{step_op.col}")
        step_val  = self._expr()
        pure2     = step_op.value[:-1] if step_op.value != "=" else ""
        step      = Assign(step_name, pure2, step_val)
        self._expect(")")

        body = self._block()
        return ForStmt(init, cond, step, body)

    def _foreach_stmt(self):
        self._advance()  # consume 'foreach'
        self._expect("(")
        var = self._expect("IDENT").value
        self._expect("IN")
        iterable = self._expr()
        self._expect(")")
        body = self._block()
        return ForEachStmt(var, iterable, body)

    def _func_decl(self):
        self._advance()
        ret_type = self._parse_type()
        name     = self._expect("IDENT").value
        self._expect("(")
        params   = []
        variadic = False
        if not self._match(")"):
            ptype = self._parse_type()
            # Check for variadic: TYPE* name
            if self._match("*"):
                self._advance()
                variadic = True
            pname = self._expect("IDENT").value
            params.append((ptype, pname, variadic))
            if not variadic:
                while self._match(","):
                    self._advance()
                    pt = self._parse_type()
                    is_var = False
                    if self._match("*"):
                        self._advance()
                        is_var = True
                    pn = self._expect("IDENT").value
                    params.append((pt, pn, is_var))
                    if is_var:
                        variadic = True
                        break
        self._expect(")")
        body = self._block()
        return FuncDecl(ret_type, name, params, body, variadic)

    def _return_stmt(self):
        self._advance()
        if self._match(";"):
            self._advance()
            return ReturnStmt(None)
        val = self._expr()
        self._expect(";")
        return ReturnStmt(val)

    def _yeet_stmt(self):
        self._advance()
        val = self._expr()
        self._expect(";")
        return YeetStmt(val)

    def _shield_stmt(self):
        self._advance()  # consume 'shield'
        body = self._block()
        self._expect("MISS")
        self._expect("(")
        err_name = self._expect("IDENT").value
        self._expect(")")
        catch_body = self._block()
        return ShieldStmt(body, err_name, catch_body)

    def _expr_stmt(self):
        expr = self._expr()
        self._expect(";")
        return ExprStmt(expr)

    # ── Expression parser ──────────────────────────────────────
    def _expr(self):
        return self._ternary()

    def _ternary(self):
        """cond ?? then :: else"""
        left = self._or_expr()
        if self._match(".."):
            # Using '..' as ternary separator: cond ?? expr :: expr
            pass
        # ternary: condition ?? thenExpr :: elseExpr
        # Let's use the token sequence: expr if_kw expr else_kw expr is complex
        # Instead: we support (cond) ? expr : expr via '?' and ':'
        # Since '?' is not in our lexer, skip ternary for now — already covered by if/else
        return left

    def _or_expr(self):
        left = self._and_expr()
        while self._match("||"):
            op = self._advance().value
            left = BinOp(op, left, self._and_expr())
        return left

    def _and_expr(self):
        left = self._cmp_expr()
        while self._match("&&"):
            op = self._advance().value
            left = BinOp(op, left, self._cmp_expr())
        return left

    def _cmp_expr(self):
        left = self._add_expr()
        while self._match("==", "!=", "<", ">", "<=", ">="):
            op = self._advance().value
            left = BinOp(op, left, self._add_expr())
        return left

    def _add_expr(self):
        left = self._mul_expr()
        while self._match("+", "-"):
            op = self._advance().value
            left = BinOp(op, left, self._mul_expr())
        return left

    def _mul_expr(self):
        left = self._pow_expr()
        while self._match("*", "/", "%"):
            op = self._advance().value
            left = BinOp(op, left, self._pow_expr())
        return left

    def _pow_expr(self):
        base = self._unary_expr()
        if self._match("**"):
            op = self._advance().value
            exp = self._pow_expr()  # right-associative
            return BinOp(op, base, exp)
        return base

    def _unary_expr(self):
        if self._match("!"):
            op = self._advance().value
            return UnaryOp(op, self._unary_expr())
        if self._match("-"):
            self._advance()
            return UnaryOp("neg", self._unary_expr())
        return self._postfix()

    def _postfix(self):
        """Handle method calls and index accesses: expr.method(args) and expr[index]"""
        node = self._primary()
        while True:
            if self._match("."):
                self._advance()
                method = self._expect("IDENT").value
                self._expect("(")
                args = []
                if not self._match(")"):
                    args.append(self._expr())
                    while self._match(","):
                        self._advance()
                        args.append(self._expr())
                self._expect(")")
                node = MethodCall(node, method, args)
            elif self._match("["):
                self._advance()
                idx = self._expr()
                self._expect("]")
                node = IndexGet(node, idx)
            else:
                break
        return node

    def _primary(self):
        tok = self._peek()

        if tok.type == "NUMBER":
            self._advance()
            v = tok.value
            return Literal(float(v) if "." in v else int(v))

        if tok.type == "STRING":
            self._advance()
            return Literal(tok.value)

        if tok.type == "FR":
            self._advance()
            return Literal(True)

        if tok.type == "CAP":
            self._advance()
            return Literal(False)

        if tok.type == "NADA":
            self._advance()
            return NullLiteral()

        # Array literal
        if tok.type == "[":
            self._advance()
            elements = []
            if not self._match("]"):
                elements.append(self._expr())
                while self._match(","):
                    self._advance()
                    if self._match("]"): break  # trailing comma OK
                    elements.append(self._expr())
            self._expect("]")
            return ArrayLiteral(elements)

        if tok.type == "CATCH":
            self._advance()
            self._expect("(")
            prompt = self._expr()
            self._expect(")")
            return CatchExpr(prompt)

        if tok.type == "CATCHNUM":
            self._advance()
            self._expect("(")
            prompt = self._expr()
            self._expect(")")
            return CatchNumExpr(prompt)

        if tok.type == "IDENT":
            name = self._advance().value
            if self._match("("):
                self._advance()
                args = []
                if not self._match(")"):
                    args.append(self._expr())
                    while self._match(","):
                        self._advance()
                        args.append(self._expr())
                self._expect(")")
                return Call(name, args)
            return Var(name)

        if tok.type == "(":
            self._advance()
            expr = self._expr()
            self._expect(")")
            return expr

        raise ParserError(
            f"Unexpected token '{tok.value}' ({tok.type}) in expression at {tok.line}:{tok.col}"
        )


# ═══════════════════════════════════════════════════════════════
#  RUNTIME
# ═══════════════════════════════════════════════════════════════

class CanError(RuntimeError): pass
class UserYeet(Exception):
    """User-thrown error via yeet"""
    def __init__(self, value): self.value = value
class ReturnSignal(Exception):
    def __init__(self, value): self.value = value
class BreakSignal(Exception):    pass
class ContinueSignal(Exception): pass

class CanArray:
    """Mutable array wrapper so we can pass by reference semantics"""
    def __init__(self, elements: list):
        self.elements = list(elements)
    def __repr__(self):
        return f"[{', '.join(repr(e) for e in self.elements)}]"
    def __len__(self):
        return len(self.elements)

class Environment:
    def __init__(self, parent=None):
        self._vars = {}
        self.parent = parent

    def declare(self, dtype, name, value):
        if name in self._vars:
            raise CanError(f"Variable '{name}' is already declared in this scope")
        self._vars[name] = (dtype, value)

    def assign(self, name, value):
        if name in self._vars:
            dtype = self._vars[name][0]
            _type_check(dtype, name, value)
            self._vars[name] = (dtype, value)
        elif self.parent is not None:
            self.parent.assign(name, value)
        else:
            raise CanError(f"Undefined variable '{name}'")

    def get(self, name):
        if name in self._vars:
            return self._vars[name][1]
        if self.parent is not None:
            return self.parent.get(name)
        raise CanError(f"Undefined variable '{name}'")

    def get_type(self, name):
        if name in self._vars:
            return self._vars[name][0]
        if self.parent is not None:
            return self.parent.get_type(name)
        raise CanError(f"Undefined variable '{name}'")

class CanFunction:
    def __init__(self, decl, closure):
        self.decl    = decl
        self.closure = closure

_PY_TYPE = {bool: "yap", int: "etco", float: "etco", str: "Ower", type(None): "nada", CanArray: "rack"}

def _can_type(val):
    return _PY_TYPE.get(type(val), "unknown")

def _type_check(dtype, name, val):
    if dtype == "yap":        ok = isinstance(val, bool)
    elif dtype == "etco":     ok = isinstance(val, (int, float)) and not isinstance(val, bool)
    elif dtype == "Ower":     ok = isinstance(val, str)
    elif dtype == "nada":     ok = val is None
    elif dtype == "rack":     ok = isinstance(val, CanArray)
    elif dtype == "__func__": ok = isinstance(val, CanFunction)
    else:                     ok = True
    if not ok:
        raise CanError(f"Type error: '{name}' expects {dtype} but got {_can_type(val)} ({val!r})")


# ═══════════════════════════════════════════════════════════════
#  INTERPRETER
# ═══════════════════════════════════════════════════════════════

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self._builtins = {
            # Conversion
            "len":      self._bi_len,
            "toOwer":   self._bi_to_ower,
            "toEtco":   self._bi_to_etco,
            "toYap":    self._bi_to_yap,
            # Math
            "floor":    self._bi_floor,
            "ceil":     self._bi_ceil,
            "round":    self._bi_round_fn,
            "abs":      self._bi_abs,
            "max":      self._bi_max,
            "min":      self._bi_min,
            "pow":      self._bi_pow,
            "sqrt":     self._bi_sqrt,
            "log":      self._bi_log,
            "sin":      self._bi_sin,
            "cos":      self._bi_cos,
            "tan":      self._bi_tan,
            # Random
            "randInt":  self._bi_randint,
            "randNum":  self._bi_randnum,
            # Array
            "newRack":  self._bi_rack,
            "range":    self._bi_range,
            # String
            "chars":    self._bi_chars,
            # I/O
            "exit":     self._bi_exit,
            "clock":    self._bi_clock,
            # Type checking
            "isYap":    lambda a: (self._arity("isYap", a, 1), isinstance(a[0], bool))[1],
            "isEtco":   lambda a: (self._arity("isEtco", a, 1), isinstance(a[0], (int, float)) and not isinstance(a[0], bool))[1],
            "isOwer":   lambda a: (self._arity("isOwer", a, 1), isinstance(a[0], str))[1],
            "isNada":   lambda a: (self._arity("isNada", a, 1), a[0] is None)[1],
            "isRack":   lambda a: (self._arity("isRack", a, 1), isinstance(a[0], CanArray))[1],
            "typeOf":   self._bi_typeof,
        }
        # String methods
        self._str_methods = {
            "len":       lambda s, a: len(s),
            "upper":     lambda s, a: s.upper(),
            "lower":     lambda s, a: s.lower(),
            "trim":      lambda s, a: s.strip(),
            "trimLeft":  lambda s, a: s.lstrip(),
            "trimRight": lambda s, a: s.rstrip(),
            "reverse":   lambda s, a: s[::-1],
            "contains":  lambda s, a: (self._m_arity("contains", a, 1), s.__contains__(a[0]))[1],
            "startsWith":lambda s, a: (self._m_arity("startsWith", a, 1), s.startswith(a[0]))[1],
            "endsWith":  lambda s, a: (self._m_arity("endsWith", a, 1), s.endswith(a[0]))[1],
            "indexOf":   lambda s, a: (self._m_arity("indexOf", a, 1), s.find(a[0]))[1],
            "slice":     self._sm_slice,
            "replace":   lambda s, a: (self._m_arity("replace", a, 2), s.replace(a[0], a[1]))[1],
            "split":     self._sm_split,
            "repeat":    lambda s, a: (self._m_arity("repeat", a, 1), s * int(a[0]))[1],
            "charAt":    lambda s, a: (self._m_arity("charAt", a, 1), s[int(a[0])] if 0 <= int(a[0]) < len(s) else "")[1],
            "toNum":     lambda s, a: (float(s) if "." in s else int(s)),
        }
        # Array methods
        self._arr_methods = {
            "len":      lambda arr, a: len(arr.elements),
            "push":     self._am_push,
            "pop":      self._am_pop,
            "shift":    self._am_shift,
            "unshift":  self._am_unshift,
            "get":      lambda arr, a: (self._m_arity("get", a, 1), arr.elements[int(a[0])])[1],
            "set":      self._am_set,
            "slice":    self._am_slice,
            "contains": lambda arr, a: (self._m_arity("contains", a, 1), a[0] in arr.elements)[1],
            "indexOf":  lambda arr, a: (self._m_arity("indexOf", a, 1), arr.elements.index(a[0]) if a[0] in arr.elements else -1)[1],
            "reverse":  self._am_reverse,
            "join":     self._am_join,
            "copy":     lambda arr, a: CanArray(arr.elements[:]),
            "clear":    self._am_clear,
            "first":    lambda arr, a: arr.elements[0] if arr.elements else None,
            "last":     lambda arr, a: arr.elements[-1] if arr.elements else None,
            "isEmpty":  lambda arr, a: len(arr.elements) == 0,
            "concat":   self._am_concat,
        }

    # ── Method helpers ───────────────────────────────────────
    def _m_arity(self, name, args, n):
        if len(args) != n:
            raise CanError(f".{name}() takes {n} argument(s), got {len(args)}")

    def _sm_slice(self, s, a):
        if len(a) == 1: return s[int(a[0]):]
        if len(a) == 2: return s[int(a[0]):int(a[1])]
        raise CanError("slice() takes 1 or 2 args")

    def _sm_split(self, s, a):
        if not a: return CanArray(list(s))
        self._m_arity("split", a, 1)
        return CanArray(s.split(a[0]))

    def _am_push(self, arr, a):
        if not a: raise CanError("push() needs at least 1 argument")
        for x in a: arr.elements.append(x)
        return len(arr.elements)

    def _am_pop(self, arr, a):
        if not arr.elements: raise CanError("pop() on empty rack")
        return arr.elements.pop()

    def _am_shift(self, arr, a):
        if not arr.elements: raise CanError("shift() on empty rack")
        return arr.elements.pop(0)

    def _am_unshift(self, arr, a):
        if not a: raise CanError("unshift() needs at least 1 argument")
        for x in reversed(a): arr.elements.insert(0, x)
        return len(arr.elements)

    def _am_set(self, arr, a):
        self._m_arity("set", a, 2)
        idx = int(a[0])
        if idx < 0 or idx >= len(arr.elements):
            raise CanError(f"rack index {idx} out of bounds (size {len(arr.elements)})")
        arr.elements[idx] = a[1]
        return a[1]

    def _am_slice(self, arr, a):
        if len(a) == 1: return CanArray(arr.elements[int(a[0]):])
        if len(a) == 2: return CanArray(arr.elements[int(a[0]):int(a[1])])
        raise CanError("slice() takes 1 or 2 args")

    def _am_reverse(self, arr, a):
        arr.elements.reverse()
        return arr

    def _am_join(self, arr, a):
        sep = a[0] if a else " "
        return sep.join(self._str(x) for x in arr.elements)

    def _am_clear(self, arr, a):
        arr.elements.clear()
        return None

    def _am_concat(self, arr, a):
        self._m_arity("concat", a, 1)
        if not isinstance(a[0], CanArray):
            raise CanError("concat() expects a rack")
        return CanArray(arr.elements + a[0].elements)

    # ── Built-ins ────────────────────────────────────────────
    def _arity(self, name, args, n):
        if len(args) != n:
            raise CanError(f"{name}() takes {n} argument(s), got {len(args)}")

    def _assert_num(self, v, ctx):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise CanError(f"{ctx}: expected etco, got {_can_type(v)}")
        return v

    def _bi_len(self, a):
        self._arity("len", a, 1)
        v = a[0]
        if isinstance(v, str): return len(v)
        if isinstance(v, CanArray): return len(v.elements)
        raise CanError(f"len() expects Ower or rack, got {_can_type(v)}")

    def _bi_to_ower(self, a):
        self._arity("toOwer", a, 1)
        return self._str(a[0])

    def _bi_to_etco(self, a):
        self._arity("toEtco", a, 1)
        v = a[0]
        if isinstance(v, bool): return 1 if v else 0
        if isinstance(v, (int, float)): return v
        if isinstance(v, str):
            try: return float(v) if "." in v else int(v)
            except ValueError: pass
        raise CanError(f"Cannot convert {v!r} to etco")

    def _bi_to_yap(self, a):
        self._arity("toYap", a, 1)
        v = a[0]
        if isinstance(v, bool): return v
        if isinstance(v, (int, float)): return v != 0
        if isinstance(v, str): return v.lower() in ("fr", "true", "1", "yes")
        if isinstance(v, CanArray): return len(v.elements) > 0
        return False

    def _bi_floor(self, a):
        self._arity("floor", a, 1)
        return int(math.floor(self._assert_num(a[0], "floor")))

    def _bi_ceil(self, a):
        self._arity("ceil", a, 1)
        return int(math.ceil(self._assert_num(a[0], "ceil")))

    def _bi_round_fn(self, a):
        if len(a) not in (1, 2): raise CanError("round() takes 1 or 2 arguments")
        return round(self._assert_num(a[0], "round"), int(a[1]) if len(a)==2 else 0)

    def _bi_abs(self, a):
        self._arity("abs", a, 1); return abs(self._assert_num(a[0], "abs"))

    def _bi_max(self, a):
        if len(a) == 1 and isinstance(a[0], CanArray):
            if not a[0].elements: raise CanError("max() on empty rack")
            return max(self._assert_num(v, "max") for v in a[0].elements)
        if len(a) < 2: raise CanError("max() needs at least 2 arguments or 1 rack")
        return max(self._assert_num(v, "max") for v in a)

    def _bi_min(self, a):
        if len(a) == 1 and isinstance(a[0], CanArray):
            if not a[0].elements: raise CanError("min() on empty rack")
            return min(self._assert_num(v, "min") for v in a[0].elements)
        if len(a) < 2: raise CanError("min() needs at least 2 arguments or 1 rack")
        return min(self._assert_num(v, "min") for v in a)

    def _bi_pow(self, a):
        self._arity("pow", a, 2)
        return self._assert_num(a[0], "pow") ** self._assert_num(a[1], "pow")

    def _bi_sqrt(self, a):
        self._arity("sqrt", a, 1)
        v = self._assert_num(a[0], "sqrt")
        if v < 0: raise CanError("sqrt() of negative number")
        return math.sqrt(v)

    def _bi_log(self, a):
        if len(a) == 1: return math.log(self._assert_num(a[0], "log"))
        if len(a) == 2: return math.log(self._assert_num(a[0], "log"), self._assert_num(a[1], "log"))
        raise CanError("log() takes 1 or 2 args")

    def _bi_sin(self, a):
        self._arity("sin", a, 1); return math.sin(self._assert_num(a[0], "sin"))

    def _bi_cos(self, a):
        self._arity("cos", a, 1); return math.cos(self._assert_num(a[0], "cos"))

    def _bi_tan(self, a):
        self._arity("tan", a, 1); return math.tan(self._assert_num(a[0], "tan"))

    def _bi_randint(self, a):
        self._arity("randInt", a, 2)
        return random.randint(int(self._assert_num(a[0], "randInt")),
                              int(self._assert_num(a[1], "randInt")))

    def _bi_randnum(self, a):
        if not a: return random.random()
        if len(a) == 2:
            lo = self._assert_num(a[0], "randNum")
            hi = self._assert_num(a[1], "randNum")
            return random.uniform(lo, hi)
        raise CanError("randNum() takes 0 or 2 args")

    def _bi_rack(self, a):
        """newRack(size) or newRack(size, fillValue) → new array"""
        if len(a) == 0: return CanArray([])
        if len(a) == 1:
            n = int(self._assert_num(a[0], "rack"))
            return CanArray([None] * n)
        if len(a) == 2:
            n   = int(self._assert_num(a[0], "rack"))
            val = a[1]
            return CanArray([val] * n)
        raise CanError("rack() takes 0, 1, or 2 args")

    def _bi_range(self, a):
        if len(a) == 1:
            return CanArray(list(range(int(self._assert_num(a[0], "range")))))
        if len(a) == 2:
            return CanArray(list(range(int(self._assert_num(a[0], "range")),
                                       int(self._assert_num(a[1], "range")))))
        if len(a) == 3:
            return CanArray(list(range(int(self._assert_num(a[0], "range")),
                                       int(self._assert_num(a[1], "range")),
                                       int(self._assert_num(a[2], "range")))))
        raise CanError("range() takes 1, 2, or 3 args")

    def _bi_chars(self, a):
        self._arity("chars", a, 1)
        if not isinstance(a[0], str): raise CanError("chars() expects Ower")
        return CanArray(list(a[0]))

    def _bi_exit(self, a):
        sys.exit(int(a[0]) if a else 0)

    def _bi_clock(self, a):
        return time.time()

    def _bi_typeof(self, a):
        self._arity("typeOf", a, 1)
        return _can_type(a[0])

    # ── Run ──────────────────────────────────────────────────
    def run(self, program):
        for stmt in program.stmts:
            self._exec(stmt, self.globals)

    def _exec_block(self, block, env):
        for stmt in block.stmts:
            self._exec(stmt, env)

    def _exec(self, node, env):
        # ── Spill (print) ─────────────────────────────────────
        if isinstance(node, Spill):
            text = " ".join(self._str(self._eval(e, env)) for e in node.exprs)
            if node.newline:
                print(text)
            else:
                print(text, end="", flush=True)
            return

        # ── Variable declaration ──────────────────────────────
        if isinstance(node, VarDecl):
            val = self._eval(node.value, env)
            _type_check(node.dtype, node.name, val)
            env.declare(node.dtype, node.name, val)
            return

        # ── Assignment ────────────────────────────────────────
        if isinstance(node, Assign):
            new_val = self._eval(node.value, env)
            if node.index is not None:
                # Array index assignment: arr[i] = val
                arr = env.get(node.name)
                if not isinstance(arr, CanArray):
                    raise CanError(f"'{node.name}' is not a rack")
                idx = int(self._eval(node.index, env))
                if idx < 0 or idx >= len(arr.elements):
                    raise CanError(f"Index {idx} out of bounds (size {len(arr.elements)})")
                arr.elements[idx] = new_val
                return
            if node.op == "":
                result = new_val
            else:
                cur = env.get(node.name)
                result = self._compound(node.op, cur, new_val, node.name)
            env.assign(node.name, result)
            return

        # ── If / else-if / else ───────────────────────────────
        if isinstance(node, IfStmt):
            for cond, body in node.branches:
                val = self._eval(cond, env)
                if not isinstance(val, bool):
                    raise CanError(f"Condition must be yap, got {_can_type(val)}")
                if val:
                    self._exec_block(body, Environment(env))
                    return
            if node.else_block:
                self._exec_block(node.else_block, Environment(env))
            return

        # ── While ─────────────────────────────────────────────
        if isinstance(node, WhileStmt):
            while True:
                val = self._eval(node.cond, env)
                if not isinstance(val, bool):
                    raise CanError(f"ghost condition must be yap, got {_can_type(val)}")
                if not val: break
                try:
                    self._exec_block(node.body, Environment(env))
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        # ── Do-While ──────────────────────────────────────────
        if isinstance(node, DoWhileStmt):
            while True:
                try:
                    self._exec_block(node.body, Environment(env))
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                val = self._eval(node.cond, env)
                if not isinstance(val, bool):
                    raise CanError(f"grind condition must be yap, got {_can_type(val)}")
                if not val: break
            return

        # ── For ───────────────────────────────────────────────
        if isinstance(node, ForStmt):
            loop_env = Environment(env)
            init = node.init
            init_val = self._eval(init.value, loop_env)
            if init.op != "":
                cur = loop_env.get(init.name)
                init_val = self._compound(init.op, cur, init_val, init.name)
            try:
                loop_env.assign(init.name, init_val)
            except CanError:
                loop_env.declare("etco", init.name, init_val)
            while True:
                val = self._eval(node.cond, loop_env)
                if not isinstance(val, bool):
                    raise CanError(f"slide condition must be yap, got {_can_type(val)}")
                if not val: break
                try:
                    self._exec_block(node.body, Environment(loop_env))
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                self._exec(node.step, loop_env)
            return

        # ── For-Each ──────────────────────────────────────────
        if isinstance(node, ForEachStmt):
            iterable = self._eval(node.iterable, env)
            if isinstance(iterable, str):
                items = list(iterable)
            elif isinstance(iterable, CanArray):
                items = iterable.elements
            else:
                raise CanError(f"foreach expects Ower or rack, got {_can_type(iterable)}")
            for item in items:
                loop_env = Environment(env)
                # Declare loop variable dynamically
                loop_env.declare(_can_type(item) if not isinstance(item, bool) else "yap",
                                 node.var, item)
                try:
                    self._exec_block(node.body, loop_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        # ── Function declaration ──────────────────────────────
        if isinstance(node, FuncDecl):
            env.declare("__func__", node.name, CanFunction(node, env))
            return

        # ── Return ────────────────────────────────────────────
        if isinstance(node, ReturnStmt):
            raise ReturnSignal(self._eval(node.value, env) if node.value else None)

        # ── Break / Continue ──────────────────────────────────
        if isinstance(node, BreakStmt):    raise BreakSignal()
        if isinstance(node, ContinueStmt): raise ContinueSignal()

        # ── Yeet (throw) ──────────────────────────────────────
        if isinstance(node, YeetStmt):
            val = self._eval(node.value, env)
            raise UserYeet(val)

        # ── Shield (try/catch) ────────────────────────────────
        if isinstance(node, ShieldStmt):
            try:
                self._exec_block(node.body, Environment(env))
            except UserYeet as uy:
                err_env = Environment(env)
                err_env.declare("Ower", node.err_name, self._str(uy.value))
                self._exec_block(node.catch_body, err_env)
            except CanError as ce:
                err_env = Environment(env)
                err_env.declare("Ower", node.err_name, str(ce))
                self._exec_block(node.catch_body, err_env)
            return

        # ── Expression statement ──────────────────────────────
        if isinstance(node, ExprStmt):
            self._eval(node.expr, env)
            return

        raise CanError(f"Unknown statement: {type(node).__name__}")

    def _compound(self, op, cur, new_val, name):
        if op == "+":  return self._add(cur, new_val, name)
        if op == "-":  return self._arith("-", cur, new_val)
        if op == "*":  return self._arith("*", cur, new_val)
        if op == "/":  return self._div(cur, new_val)
        if op == "%":  return self._arith("%", cur, new_val)
        if op == "**": return self._assert_num(cur, name) ** self._assert_num(new_val, name)
        raise CanError(f"Unknown compound operator '{op}='")

    # ── Eval (expressions) ───────────────────────────────────
    def _eval(self, node, env):
        if isinstance(node, Literal):     return node.value
        if isinstance(node, NullLiteral): return None

        if isinstance(node, ArrayLiteral):
            return CanArray([self._eval(e, env) for e in node.elements])

        if isinstance(node, Var):
            return env.get(node.name)

        if isinstance(node, IndexGet):
            obj = self._eval(node.obj, env)
            idx = self._eval(node.index, env)
            if isinstance(obj, CanArray):
                i = int(idx)
                if i < 0: i += len(obj.elements)
                if i < 0 or i >= len(obj.elements):
                    raise CanError(f"Index {int(idx)} out of bounds (size {len(obj.elements)})")
                return obj.elements[i]
            if isinstance(obj, str):
                i = int(idx)
                if i < 0: i += len(obj)
                if i < 0 or i >= len(obj):
                    raise CanError(f"Index {int(idx)} out of bounds (size {len(obj)})")
                return obj[i]
            raise CanError(f"Cannot index into {_can_type(obj)}")

        if isinstance(node, BinOp):
            l = self._eval(node.left, env)
            if node.op == "&&":
                if not isinstance(l, bool):
                    raise CanError("'&&' requires yap operands")
                if not l:
                    return False
            elif node.op == "||":
                if not isinstance(l, bool):
                    raise CanError("'||' requires yap operands")
                if l:
                    return True
            r = self._eval(node.right, env)
            return self._binop(node.op, l, r)

        if isinstance(node, UnaryOp):
            v = self._eval(node.operand, env)
            if node.op == "!":
                if not isinstance(v, bool): raise CanError(f"'!' requires yap")
                return not v
            if node.op == "neg":
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise CanError(f"Unary '-' requires etco")
                return -v

        if isinstance(node, MethodCall):
            obj = self._eval(node.obj, env)
            args = [self._eval(a, env) for a in node.args]
            return self._method_call(obj, node.method, args)

        if isinstance(node, Call):
            return self._call(node, env)

        if isinstance(node, CatchExpr):
            prompt = self._str(self._eval(node.prompt, env))
            try:    return input(prompt)
            except EOFError: return ""

        if isinstance(node, CatchNumExpr):
            prompt = self._str(self._eval(node.prompt, env))
            try:    raw = input(prompt).strip()
            except EOFError: raw = "0"
            try:    return float(raw) if "." in raw else int(raw)
            except ValueError: raise CanError(f"catchNum: '{raw}' is not a valid number")

        raise CanError(f"Unknown expression: {type(node).__name__}")

    def _method_call(self, obj, method, args):
        try:
            if isinstance(obj, str):
                if method not in self._str_methods:
                    raise CanError(f"Ower has no method '{method}'")
                return self._str_methods[method](obj, args)
            if isinstance(obj, CanArray):
                if method not in self._arr_methods:
                    raise CanError(f"rack has no method '{method}'")
                return self._arr_methods[method](obj, args)
            raise CanError(f"{_can_type(obj)} has no methods")
        except CanError:
            raise
        except (IndexError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
            raise CanError(f".{method}() failed: {exc}") from None

    def _binop(self, op, l, r):
        if op == "+":  return self._add(l, r, "expression")
        if op == "-":  return self._arith(op, l, r)
        if op == "*":
            # String * number repeat
            if isinstance(l, str) and isinstance(r, (int, float)) and not isinstance(r, bool):
                return l * int(r)
            return self._arith(op, l, r)
        if op == "/":  return self._div(l, r)
        if op == "%":  return self._arith(op, l, r)
        if op == "**":
            return self._assert_num(l, "**") ** self._assert_num(r, "**")
        if op == "==": return l == r
        if op == "!=": return l != r
        if op in ("<", ">", "<=", ">="):
            if type(l) != type(r) and not (isinstance(l, (int, float)) and isinstance(r, (int, float))):
                raise CanError(f"Cannot compare {_can_type(l)} with {_can_type(r)}")
            if op == "<":  return l < r
            if op == ">":  return l > r
            if op == "<=": return l <= r
            if op == ">=": return l >= r
        if op == "&&":
            if not isinstance(l, bool) or not isinstance(r, bool):
                raise CanError("'&&' requires yap operands")
            return l and r
        if op == "||":
            if not isinstance(l, bool) or not isinstance(r, bool):
                raise CanError("'||' requires yap operands")
            return l or r
        raise CanError(f"Unknown operator '{op}'")

    def _add(self, l, r, ctx):
        if (isinstance(l, (int, float)) and not isinstance(l, bool) and
                isinstance(r, (int, float)) and not isinstance(r, bool)):
            return l + r
        if isinstance(l, str) and isinstance(r, str): return l + r
        if isinstance(l, str): return l + self._str(r)
        if isinstance(r, str): return self._str(l) + r
        if isinstance(l, CanArray) and isinstance(r, CanArray):
            return CanArray(l.elements + r.elements)
        raise CanError(f"'+' cannot operate on {_can_type(l)} and {_can_type(r)}")

    def _arith(self, op, l, r):
        if isinstance(l, bool) or not isinstance(l, (int, float)):
            raise CanError(f"'{op}' requires etco, got {_can_type(l)}")
        if isinstance(r, bool) or not isinstance(r, (int, float)):
            raise CanError(f"'{op}' requires etco, got {_can_type(r)}")
        if op == "-": return l - r
        if op == "*": return l * r
        if op == "%":
            if r == 0: raise CanError("Modulo by zero")
            return l % r

    def _div(self, l, r):
        if isinstance(l, bool) or not isinstance(l, (int, float)):
            raise CanError(f"'/' requires etco, got {_can_type(l)}")
        if isinstance(r, bool) or not isinstance(r, (int, float)):
            raise CanError(f"'/' requires etco, got {_can_type(r)}")
        if r == 0: raise CanError("Division by zero")
        result = l / r
        if isinstance(l, int) and isinstance(r, int) and result == int(result):
            return int(result)
        return result

    def _call(self, node, env):
        if node.name in self._builtins:
            args = [self._eval(a, env) for a in node.args]
            try:
                return self._builtins[node.name](args)
            except CanError:
                raise
            except (IndexError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
                raise CanError(f"{node.name}() failed: {exc}") from None

        try:
            fn = env.get(node.name)
        except CanError:
            raise CanError(f"Undefined function '{node.name}'")

        if not isinstance(fn, CanFunction):
            raise CanError(f"'{node.name}' is not a function")

        decl = fn.decl
        call_env = Environment(fn.closure)

        if decl.variadic:
            # Last param is variadic
            fixed_params = [(pt, pn) for pt, pn, pv in decl.params if not pv]
            var_param    = next(((pt, pn) for pt, pn, pv in decl.params if pv), None)
            if len(node.args) < len(fixed_params):
                raise CanError(f"'{node.name}' expects at least {len(fixed_params)} arg(s)")
            for (ptype, pname), arg_expr in zip(fixed_params, node.args[:len(fixed_params)]):
                val = self._eval(arg_expr, env)
                _type_check(ptype, pname, val)
                call_env.declare(ptype, pname, val)
            if var_param:
                rest = CanArray([self._eval(a, env) for a in node.args[len(fixed_params):]])
                call_env.declare("rack", var_param[1], rest)
        else:
            fixed_params = [(pt, pn) for pt, pn, _ in decl.params]
            if len(node.args) != len(fixed_params):
                raise CanError(
                    f"'{node.name}' expects {len(fixed_params)} arg(s), got {len(node.args)}"
                )
            for (ptype, pname), arg_expr in zip(fixed_params, node.args):
                val = self._eval(arg_expr, env)
                _type_check(ptype, pname, val)
                call_env.declare(ptype, pname, val)

        ret_val = None
        try:
            self._exec_block(decl.body, call_env)
        except ReturnSignal as rs:
            ret_val = rs.value

        if decl.ret_type != "nada":
            if ret_val is None:
                raise CanError(f"Function '{node.name}' declared {decl.ret_type} but returned nada")
            _type_check(decl.ret_type, f"return of {node.name}", ret_val)
        return ret_val

    def _str(self, x):
        if isinstance(x, bool):    return "fr" if x else "cap"
        if x is None:              return "nada"
        if isinstance(x, CanArray):
            inner = ", ".join(self._str(e) for e in x.elements)
            return f"[{inner}]"
        if isinstance(x, float):
            if x == int(x):        return str(int(x))
            return f"{x:.10g}"
        return str(x)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def run_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr); sys.exit(1)

    try:    tokens = Lexer(code).tokenize()
    except LexerError as e:
        print(f"Lexer error: {e}", file=sys.stderr); sys.exit(1)

    try:    tree = Parser(tokens).parse()
    except ParserError as e:
        print(f"Parser error: {e}", file=sys.stderr); sys.exit(1)

    interp = Interpreter()
    try:
        interp.run(tree)
    except CanError as e:
        print(f"Runtime error: {e}", file=sys.stderr); sys.exit(1)
    except UserYeet as uy:
        print(f"Unhandled yeet: {uy.value}", file=sys.stderr); sys.exit(1)
    except (BreakSignal, ContinueSignal):
        print("Runtime error: 'drop'/'skip' used outside a loop.", file=sys.stderr); sys.exit(1)
    except ReturnSignal:
        print("Runtime error: 'bounce' used outside a function.", file=sys.stderr); sys.exit(1)
    except RecursionError:
        print("Runtime error: Stack overflow (too much recursion).", file=sys.stderr); sys.exit(1)


def run_repl():
    print("CAN v2.0 REPL  (Ctrl+C or Ctrl+D to exit, end line with \\ to continue)")
    print("Type 'help' for quick reference.\n")
    interp = Interpreter()
    buf = ""
    try:
        import readline  # enables arrow keys, history on supported platforms
    except ImportError:
        pass
    while True:
        try:
            line = input("... " if buf else "can> ")
            if line.strip() == "help":
                _print_quickref()
                buf = ""
                continue
            if line.strip() == "clear":
                interp = Interpreter()
                print("(Environment cleared)")
                buf = ""
                continue
            if line.endswith("\\"):
                buf += line[:-1] + "\n"; continue
            buf += line + "\n"
        except (KeyboardInterrupt, EOFError):
            print(); break
        code = buf.strip(); buf = ""
        if not code: continue
        try:
            tokens = Lexer(code).tokenize()
            tree   = Parser(tokens).parse()
            interp.run(tree)
        except (LexerError, ParserError, CanError) as e:
            print(f"Error: {e}")
        except UserYeet as uy:
            print(f"Unhandled yeet: {uy.value}")
        except (BreakSignal, ContinueSignal):
            print("Error: 'drop'/'skip' outside loop")
        except ReturnSignal:
            print("Error: 'bounce' outside function")


def _print_quickref():
    print("""
Quick Reference:
  think etco x = 5;         declare variable
  spill("hi", x);            print
  rack nums = [1, 2, 3];     array
  nums.push(4);               array method
  "hello".upper();            string method
  no cap (x > 0) { }         if
  ghost (x > 0) { }          while
  slide (i=0; i<5; i+=1) {}  for loop
  foreach (n in nums) { }    for-each
  grind { } ghost (cond);    do-while
  yeet "error msg";           throw error
  shield { } miss (e) { }    try/catch
  vibe etco add(etco a, etco b) { bounce a+b; }  function
  vibe nada log(Ower* args) { }  variadic
  exit | clear | help
""".strip())


def print_help():
    print("""
CAN Language v2.0 - usage:
  python canlang.py run <file.can>    Run a source file
  python canlang.py repl              Interactive REPL

-------------------------------------------------------
TYPES
  yap   bool     fr / cap
  etco  number   42  3.14
  Ower  string   "hello"
  nada  null
  rack  array    [1, 2, 3]

DECLARE     think etco x = 10;
            rack  nums = [1, 2, 3];
ASSIGN      x = 20;  x += 5;  x -= 1;  x *= 2;  x /= 4;  x **= 2;
            nums[0] = 99;

PRINT       spill("val:", x);          (with newline)
            spillRaw("no newline");     (no newline)

INPUT       think Ower s = catch("Enter: ");
            think etco n = catchNum("Enter: ");

CONDITIONALS
  no cap (x > 0) { spill("pos"); }
  lowkey (x == 0) { spill("zero"); }
  bet { spill("neg"); }

LOOPS
  ghost (x > 0) { x -= 1; }                 while
  grind { x -= 1; } ghost (x > 0);          do-while
  slide (i = 0; i < 10; i += 1) { }         for
  foreach (item in myArray) { spill(item); } for-each
  drop;   skip;                              break, continue

FUNCTIONS
  vibe etco add(etco a, etco b) { bounce a + b; }
  vibe nada greet(Ower name) { spill("Hi", name); }
  vibe nada log(Ower* args) { }            variadic

ARRAYS
  rack nums = [10, 20, 30];
  spill(nums[0]);             index read
  nums[1] = 99;               index write
  nums.push(40);  nums.pop();
  nums.len()  .contains(x)  .indexOf(x)  .slice(i, j)
  nums.reverse()  .join(", ")  .copy()  .concat(other)
  nums.first()  .last()  .isEmpty()  .clear()

STRING METHODS
  s.len()  .upper()  .lower()  .trim()  .reverse()
  s.contains(sub)  .startsWith(p)  .endsWith(s)
  s.indexOf(sub)  s.slice(i, j)  s.replace(a, b)
  s.split(sep)  .repeat(n)  .charAt(i)

ERROR HANDLING
  yeet "something went wrong";
  shield { risky(); } miss (err) { spill("Caught:", err); }

OPERATORS
  + - * / % **              arithmetic (**=power)
  == != < > <= >=           comparison
  && || !                   logical
  "abc" * 3 == "abcabcabc"  string repeat

MATH BUILT-INS
  floor(n)  ceil(n)  round(n, places)  abs(n)
  max(a,b)  min(a,b)  pow(b,e)  sqrt(n)  log(n)
  sin(n)  cos(n)  tan(n)

OTHER BUILT-INS
  len(s|arr)    toOwer(x)  toEtco(x)  toYap(x)
  rack(n, fill) range(start, end, step)  chars(str)
  randInt(lo,hi)  randNum()  randNum(lo,hi)
  typeOf(x)  isYap(x)  isEtco(x)  isOwer(x)  isNada(x)  isRack(x)
  clock()  exit(code)

COMMENTS
  ^ single line
  ... multi
      line ...
-------------------------------------------------------
""".strip())


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "run":
        run_file(args[1])
    elif len(args) == 1 and args[0] == "repl":
        run_repl()
    elif not args or args[0] in ("-h", "--help", "help"):
        print_help()
    else:
        print("Usage: python canlang.py run <file.can>  |  python canlang.py repl", file=sys.stderr)
        sys.exit(1)

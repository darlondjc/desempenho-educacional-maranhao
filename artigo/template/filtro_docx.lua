--[[
Filtro Lua do pandoc usado por build_docx.py.

Aplica ao .docx as regras de ilustrações do template da revista Debates em
Educação:
  - numeração própria por tipo, a partir do prefixo do rótulo LaTeX
    (graf: Gráfico, fig: Figura, qua: Quadro, tab: Tabela);
  - legenda acima da ilustração, com apenas "Tipo N" em negrito
    ("Gráfico 1 – Título", sem pontuação final);
  - fonte e nota abaixo, nos estilos "Fonte" e "Nota";
  - referências cruzadas (\ref) substituídas pelo número da ilustração;
  - itens de lista no estilo "Lista";
  - larguras de coluna repassadas por build_docx.py (bloco "larguras");
  - citação narrativa no padrão da NBR 10520:2023 ("Rivkin, Hanushek e
    Kain (2005)"), já que o CSL só gera a forma entre parênteses.
]]

local TIPOS = {
  graf = "Gráfico",
  fig = "Figura",
  qua = "Quadro",
  tab = "Tabela",
}

local numeros = {}   -- rótulo -> número
local contagem = {}  -- tipo -> último número usado

local function tipo_do_rotulo(id)
  local prefixo = id and id:match("^(%a+):")
  return prefixo and TIPOS[prefixo] or nil
end

local function registrar(id)
  local tipo = tipo_do_rotulo(id)
  if tipo and not numeros[id] then
    contagem[tipo] = (contagem[tipo] or 0) + 1
    numeros[id] = contagem[tipo]
  end
end

local function estilo(nome, blocos)
  return pandoc.Div(blocos, pandoc.Attr("", {}, { ["custom-style"] = nome }))
end

local function legenda(id, inlines)
  local tipo = tipo_do_rotulo(id) or "Figura"
  local rotulo = pandoc.Strong({ pandoc.Str(tipo), pandoc.Space(), pandoc.Str(tostring(numeros[id] or "?")) })
  local texto = { rotulo, pandoc.Space(), pandoc.Str("–"), pandoc.Space() }
  for _, el in ipairs(inlines) do table.insert(texto, el) end
  -- sem pontuação final no título
  local ultimo = texto[#texto]
  if ultimo and ultimo.t == "Str" then
    ultimo.text = ultimo.text:gsub("[%.;:]$", "")
  end
  return estilo("Legenda", { pandoc.Para(texto) })
end

local function inlines_da_legenda(caption)
  local inlines = {}
  for _, bloco in ipairs(caption.long or {}) do
    if bloco.content then
      for _, el in ipairs(bloco.content) do table.insert(inlines, el) end
    end
  end
  return inlines
end

local function estilizar_blocos_auxiliares(blocos)
  local saida = {}
  for _, b in ipairs(blocos) do
    if b.t == "Div" and b.classes:includes("fontebloco") then
      table.insert(saida, estilo("Fonte", b.content))
    elseif b.t == "Div" and b.classes:includes("notabloco") then
      table.insert(saida, estilo("Nota", b.content))
    elseif b.t == "Plain" or b.t == "Para" then
      table.insert(saida, estilo("Figura Imagem", { pandoc.Para(b.content) }))
    else
      table.insert(saida, b)
    end
  end
  return saida
end

-- Passo 0: aplicar as larguras de coluna (bloco "larguras" gerado por
-- build_docx.py) à tabela seguinte e remover o bloco.
local function aplicar_larguras(blocos)
  local saida, pendente = {}, nil
  for _, b in ipairs(blocos) do
    if b.t == "Div" and b.classes:includes("larguras") then
      pendente = {}
      for v in pandoc.utils.stringify(b):gmatch("[%d.]+") do
        table.insert(pendente, tonumber(v))
      end
    else
      if pendente then
        local larguras = pendente
        b = pandoc.walk_block(b, {
          Table = function(t)
            if #larguras == #t.colspecs then
              for i, spec in ipairs(t.colspecs) do
                t.colspecs[i] = { spec[1], larguras[i] }
              end
            end
            return t
          end,
        })
        pendente = nil
      end
      table.insert(saida, b)
    end
  end
  return saida
end

-- Passo 1: numerar as ilustrações na ordem em que aparecem.
local function numerar(doc)
  doc:walk({
    Figure = function(f) registrar(f.identifier) end,
    Div = function(d) registrar(d.identifier) end,
    Table = function(t) registrar(t.identifier) end,
  })
  return doc
end

-- Passo 2: montar legendas, fontes e referências cruzadas.
local function formatar(doc)
  return doc:walk({
    Link = function(l)
      if l.attributes["reference-type"] then
        local alvo = l.attributes["reference"] or l.target:gsub("^#", "")
        if numeros[alvo] then
          return pandoc.Str(tostring(numeros[alvo]))
        end
      end
    end,

    Figure = function(f)
      local blocos = { legenda(f.identifier, inlines_da_legenda(f.caption)) }
      for _, b in ipairs(estilizar_blocos_auxiliares(f.content)) do
        table.insert(blocos, b)
      end
      return blocos
    end,

    -- itens de lista: Arial 12, espaçamento 1,5, sem recuo de primeira linha
    BulletList = function(l)
      for i, item in ipairs(l.content) do l.content[i] = { estilo("Lista", item) } end
      return l
    end,
    OrderedList = function(l)
      for i, item in ipairs(l.content) do l.content[i] = { estilo("Lista", item) } end
      return l
    end,

    Div = function(d)
      -- tabela/quadro: o pandoc envolve a tabela em uma Div com o rótulo
      if tipo_do_rotulo(d.identifier) then
        local blocos = {}
        for _, b in ipairs(d.content) do
          if b.t == "Table" then
            table.insert(blocos, legenda(d.identifier, inlines_da_legenda(b.caption)))
            b.caption.long = {}
            table.insert(blocos, b)
          else
            table.insert(blocos, b)
          end
        end
        return blocos
      end
      if d.classes:includes("fontebloco") then return estilo("Fonte", d.content) end
      if d.classes:includes("notabloco") then return estilo("Nota", d.content) end
    end,
  })
end

-- Citação narrativa (\textcite): o citeproc separa os autores por ";", como
-- na citação entre parênteses. Troca o último ";" por " e" e os demais por ",".
-- Roda depois do --citeproc, que já preencheu o conteúdo da citação.
local function citacao_narrativa(c)
  if c.citations[1].mode ~= "AuthorInText" then return nil end
  local separadores = {}
  for i, el in ipairs(c.content) do
    if el.t == "Str" and el.text:sub(1, 1) == "(" then break end
    if el.t == "Str" and el.text:sub(-1) == ";" then table.insert(separadores, i) end
  end
  if #separadores == 0 then return nil end
  for j, i in ipairs(separadores) do
    local nome = c.content[i].text:sub(1, -2)
    if j < #separadores then
      c.content[i] = pandoc.Str(nome .. ",")
    else
      c.content[i] = pandoc.Str(nome)
      c.content:insert(i + 1, pandoc.Str("e"))
      c.content:insert(i + 1, pandoc.Space())
    end
  end
  return c
end

return {
  { Cite = citacao_narrativa },
  { Blocks = aplicar_larguras },
  { Pandoc = numerar },
  { Pandoc = formatar },
}

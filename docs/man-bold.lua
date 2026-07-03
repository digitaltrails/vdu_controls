-- SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
-- SPDX-License-Identifier: GPL-3.0-or-later

-- Global tracking state
local current_section = ""

-- Monitor headers to track exactly which section we are processing
function Header(elem)
  local header_text = pandoc.utils.stringify(elem.content):lower()
  if header_text:match("environment") then
    current_section = "environment"
  elseif header_text:match("files") then
    current_section = "files"
  else
    current_section = ""
  end
  return elem
end

-- Fix 1: Cover regular inline backticks universally across the document
function Code(elem)
  return pandoc.Strong(elem.text)
end

-- Fix 2: Handle properly structured native Definition Lists
function DefinitionList(elem)
  for i, item in ipairs(elem.content) do
    local term = item
    for j, inline in ipairs(term) do
      if inline.t == "Code" then
        term[j] = pandoc.Str(inline.text)
      end
    end
    elem.content[i] = pandoc.Strong(term)
  end
  return elem
end

-- Parse a raw text paragraph to turn double backticks into proper inline Code structures
local function parse_inline_backticks(text)
  local inlines = {}
  local last_pos = 1
  
  -- Find pairs of double backticks ``like this``
  for start_pos, content, end_pos in text:gmatch("()``(.-)``()") do
    if start_pos > last_pos then
      table.insert(inlines, pandoc.Str(text:sub(last_pos, start_pos - 1)))
    end
    table.insert(inlines, pandoc.Code(content))
    last_pos = end_pos
  end
  
  if last_pos <= #text then
    table.insert(inlines, pandoc.Str(text:sub(last_pos)))
  end
  
  return inlines
end

-- Fix 3: Universal multi-line parser for options, environment variables, and file paths
function CodeBlock(elem)
  -- Determine block context based on text patterns and active section headings
  local is_cli_block = elem.text:match("%-%-") or elem.text:match("%s%-")
  local is_env_block = (current_section == "environment") and (elem.text:match("%s*[A-Z_]+") ~= nil)
  local is_file_block = (current_section == "files") and (elem.text:match("[%$/]") ~= nil)

  if is_cli_block or is_env_block or is_file_block then
    local items = {}
    local current_term = nil
    local current_desc_lines = {}

    -- Helper to commit a structured term and description into the AST list
    local function save_pair()
      if current_term then
        local full_desc_text = table.concat(current_desc_lines, " "):gsub("%s+", " ")
        local processed_desc = parse_inline_backticks(full_desc_text)
        
        table.insert(items, {
          { pandoc.Strong({ pandoc.Str(current_term) }) },
          { pandoc.Plain(processed_desc) }
        })
        current_term = nil
        current_desc_lines = {}
      end
    end

    -- Loop through the block line by line
    for line in elem.text:gmatch("[^\r\n]+") do
      local trimmed = line:match("^%s*(.-)%s*$") or ""
      
      if trimmed ~= "" then
        -- Rule A: It's a CLI flag if it starts with a dash
        local is_flag = trimmed:sub(1,1) == "-"
        
        -- Rule B: It's an environment variable if it's uppercase words/commas/underscores
        local is_var = (current_section == "environment") and (trimmed:match("^[A-Z0-9_, ]+$") ~= nil)
        
        -- Rule C: It's a file path if it starts with a directory marker (/ or $)
        local first_char = trimmed:sub(1,1)
        local is_path = (current_section == "files") and (first_char == "/" or first_char == "$")

        if is_flag or is_var or is_path then
          save_pair() -- Save the previous block definition before starting a new one
          current_term = trimmed
        else
          if current_term then
            table.insert(current_desc_lines, trimmed)
          end
        end
      end
    end
    
    save_pair() -- Catch the final definition block element

    if #items > 0 then
      return pandoc.DefinitionList(items)
    end
  end
  return elem
end

function Header(elem)
  -- Track sections normally
  local header_text = pandoc.utils.stringify(elem.content):lower()
  if header_text:match("environment") then
    current_section = "environment"
  elseif header_text:match("files") then
    current_section = "files"
  else
    current_section = ""
  end

  -- Transform the Level 1 Header into a standard clean Unix NAME block
  if elem.level == 1 then
    local plain_text = pandoc.utils.stringify(elem.content)

    return {
      pandoc.Header(2, {pandoc.Str("NAME")}),
      pandoc.Para({pandoc.Str(plain_text)}) -- No manual groff string escaping needed
    }
  end

  return elem
end

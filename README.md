vim-matlab
===========

An alternative to Matlab's default editor for Vim users. I currently use it to control Comsol by running ```comsol mphserver```, launching the MATLAB REPL in Vim and running ```mphstart``` to connect them. 
Edited to function with Python 3 with fixes from Thieso from this [issue](https://github.com/daeyun/vim-matlab/issues/36).

Read the readme [upstream](https://github.com/daeyun/vim-matlab) for an overview. 

Install using Lazyvim:
```
{
    "marcusfschmidt/vim-matlab",
    build = ":UpdateRemotePlugins",
    init = function()
      vim.g.matlab_auto_mappings = 0
    end,
  },
```

In this fork, a few (likely badly implemented) changes are introduced. For example, when code is run, the cursor moves to the REPL, down to the bottom and back to the window you were in previously - this way, you can see the last executed code. If you are not running the split in vim, this might not work.


Moreover, the default keymaps are disabled. In their place, I use the below functions and keymaps written in Lua to ease cell navigation.

```
-- Function to jump to the next occurrence of a line containing "%%" as the only content
local function jump_to_next_cell_matlab()
  local current_line = vim.fn.line('.') -- Get current line number
  local total_lines = vim.fn.line('$')  -- Get total number of lines
  local found = false

  -- Loop through lines from the current line to the end
  for line = current_line + 1, total_lines do
    local line_content = vim.fn.getline(line)
    -- Check if the line contains exactly "%%" with optional leading/trailing whitespace
    if string.match(line_content, "^%s*%%%%%s*$") then
      vim.fn.cursor(line + 1, 0) -- Move cursor to the beginning of the line below
      found = true
      break
    end
  end

  -- If no occurrence is found, move cursor to the bottom of the file
  if not found then
    vim.fn.cursor(total_lines, 1) -- Move cursor to the last line
  end
end

-- Function to jump to the second-previous occurrence of a line containing "%%" as the only content
local function jump_to_previous_cell_matab()
  local current_line = vim.fn.line('.') -- Get current line number
  local found_count = 0
  local found = false

  -- Loop backward from the current line to the beginning
  for line = current_line - 1, 1, -1 do
    local line_content = vim.fn.getline(line)
    -- Check if the line contains exactly "%%" with optional leading/trailing whitespace
    if string.match(line_content, "^%s*%%%%%s*$") then
      found_count = found_count + 1
      if found_count == 2 then
        vim.fn.cursor(line + 1, 0) -- Move cursor to the beginning of the line below the second-previous occurrence
        found = true
        break
      end
    end
  end

  -- If no second-previous occurrence is found, move cursor to the top of the file
  if not found then
    vim.fn.cursor(1, 1) -- Move cursor to the first line
  end
end

-- Function to find and delete the next occurrence of a line containing "%%" as the only content
local function merge_below()
  local current_line = vim.fn.line('.')       -- Get current line number
  local total_lines = vim.fn.line('$')        -- Get total number of lines
  local saved_cursor_pos = vim.fn.getpos('.') -- Save current cursor position

  -- Loop through lines from the current line to the end
  for line = current_line + 1, total_lines do
    local line_content = vim.fn.getline(line)
    -- Check if the line contains exactly "%%" with optional leading/trailing whitespace
    if string.match(line_content, "^%s*%%%%%s*$") then
      -- Delete the line below the current line if found
      vim.cmd(tostring(line) .. "delete")

      -- Restore cursor position after deletion
      vim.fn.setpos('.', saved_cursor_pos)
      break
    end
  end
end

-- Function to find and delete the previous occurrence of a line containing "%%" as the only content
local function merge_above()
  local current_line = vim.fn.line('.')       -- Get current line number
  local saved_cursor_pos = vim.fn.getpos('.') -- Save current cursor position

  -- Loop backward from the current line to the beginning
  for line = current_line - 1, 1, -1 do
    local line_content = vim.fn.getline(line)
    -- Check if the line contains exactly "%%" with optional leading/trailing whitespace
    if string.match(line_content, "^%s*%%%%%s*$") then
      -- Delete the line above the current line if found
      vim.cmd(tostring(line) .. "delete")

      -- Restore cursor position after deletion
      vim.fn.setpos('.', saved_cursor_pos)
      break
    end
  end
end



vim.api.nvim_create_autocmd("FileType", {
  pattern = "matlab",
  callback = function(event)
  
    vim.keymap.set("n", "<leader>os", ":MatlabLaunchServer<CR>",
      { silent = true, buffer = event.buf, desc = "Start MATLAB server" })

    vim.keymap.set(
      "n",
      "<leader>cs",
      ":MatlabNormalModeCreateCell<cr>",
      { silent = true, buffer = event.buf, desc = "Split cell" }
    )

    vim.keymap.set(
      "n",
      "<leader><Space>",
      ":MatlabCliRunCell<cr>",
      { silent = true, noremap = true, buffer = event.buf, desc = "Send cell" })

    vim.keymap.set("v", "<leader><Space>", "<Esc>:MatlabCliRunSelection<cr>",
      { silent = true, buffer = event.buf, desc = "Send selection" })

    vim.keymap.set("n", "<leader>ol", ":MatlabCliRunLine<cr>",
      { silent = true, buffer = event.buf, desc = "Send line" })

    vim.keymap.set("n", "<leader>oc", ":MatlabCliCancel<cr>",
      { silent = true, buffer = event.buf, desc = "Cancel execution" })

    vim.keymap.set("n", "<leader>j", function()
        jump_to_next_cell_matlab()
      end,
      {
        silent = true,
        buffer = event.buf,
        desc = "Jump to next cell",
      })

    vim.keymap.set("n", "<leader>k", function()
        jump_to_previous_cell_matab()
      end,
      {
        silent = true,
        buffer = event.buf,
        desc = "Jump to previous cell",
      })

    vim.keymap.set("n", "<leader>cM", function()
        merge_above()
      end,
      {
        silent = true,
        buffer = event.buf,
        desc = "Merge above",
      })

    vim.keymap.set("n", "<leader>cm", function()
        merge_below()
      end,
      {
        silent = true,
        buffer = event.buf,
        desc = "Merge below",
      })
  end,
})
```

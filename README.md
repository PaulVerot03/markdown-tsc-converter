# markdown-tsc-converter
I threw this tool togetehr to help us on the last stretch
## How to use 
1) Copy-paste your content into your favourite markdown editor (i use MarkText)
2) Check that ithe headings and tables look good
3) Save your file in .md
4) Use the tool `python3 md_converter.py document.md content` where content is the name without extension of the related .tsx file
   - example : engineering success would be `python3 md_converter.py engineering.md engineering` and it will go to src/contents/engineering.tsx
5) It should find the correct file, delete everything in the return section and paste the converted code
   
Please note that i am relying on the MD editor to do char conversion (for all the greek letters)


/!\ Be careful with links and em, they will break, go over them /!\

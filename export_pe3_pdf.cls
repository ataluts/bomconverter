%%%
%
% Copyright 2014 Danil Gulin
%
% This work may be distributed and/or modified under the
% conditions of the LaTeX Project Public License, either version 1.3
% of this license or (at your option) any later version.
% The latest version of this license is in
% http://www.latex-project.org/lppl.txt
% and version 1.3 or later is part of all distributions of LaTeX
% version 2005/12/01 or later.
%
% This work has the LPPL maintenance status `maintained'.
%
% The Current Maintainer of this work is Danil Gulin.
%
% This work consists of the file xesel.cls
%
%%%

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{xesel}[2014/12/26 v1.0 Schematic Elements Listing]

% only xelatex (cyrillic strings)
\RequirePackage{ifxetex}
\RequireXeTeX

% setup base class
\LoadClass[a4paper]{article}

% setup geomtry
\RequirePackage{geometry}
\geometry{a4paper,noheadfoot,nomarginpar,top=2cm,bottom=2cm,inner=2cm,outer=.5cm}

% form drawing
\RequirePackage{atbegshi}
\RequirePackage{picture}
\RequirePackage{xcolor}

% content style
\RequirePackage{longtable}
\RequirePackage{array}

% fill form fields
\RequirePackage{rotating}

% enable free font sizing
\RequirePackage{lmodern}

% font size & style commands
\newcommand*{\XeselFontFormHeader}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontFormNames}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontFormDates}{\fontsize{3mm}{3mm}\selectfont}
\newcommand*{\XeselFontFormLetters}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontFormPages}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontFormDocDesignator}{\fontsize{10mm}{10mm}\selectfont}
\newcommand*{\XeselFontFormOrganization}{\fontsize{10mm}{10mm}\selectfont}
\newcommand*{\XeselFontFormDocName}{\fontsize{7mm}{5mm}\selectfont}
\newcommand*{\XeselFontFormDocType}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontExtraHeader}{\fontsize{5mm}{5mm}\selectfont}
\newcommand*{\XeselFontExtraData}{\fontsize{5mm}{7mm}\selectfont}
\newcommand*{\XeselFontTableHeader}{\fontsize{7mm}{4.5mm}\selectfont}
\newcommand*{\XeselFontTableData}{\fontsize{6mm}{8mm}\selectfont}

\newcommand*{\XeselFormFont}{\slshape\mdseries}
\newcommand*{\XeselDataFont}{\slshape\mdseries}

% data commands
\newcommand*{\Xesel@DocumentName}{}
\newcommand*{\Xesel@DocumentType}{}
\newcommand*{\Xesel@DocumentDesignator}{}
\newcommand*{\Xesel@LetterLeft}{}
\newcommand*{\Xesel@LetterMiddle}{}
\newcommand*{\Xesel@LetterRight}{}
\newcommand*{\Xesel@SheetIndex}{}
\newcommand*{\Xesel@SheetsTotal}{}
\newcommand*{\Xesel@Organization}{}
\newcommand*{\Xesel@ExtraActivityType}{}
\newcommand*{\Xesel@DesignerName}{}
\newcommand*{\Xesel@CheckerName}{}
\newcommand*{\Xesel@ExtraActivityName}{}
\newcommand*{\Xesel@NormativeSupervisorName}{}
\newcommand*{\Xesel@ApproverName}{}
\newcommand*{\Xesel@DesignerSignatureDate}{}
\newcommand*{\Xesel@CheckerSignatureDate}{}
\newcommand*{\Xesel@TechnicalSupervisorSignatureDate}{}
\newcommand*{\Xesel@ExtraActivitySignatureDate}{}
\newcommand*{\Xesel@NormativeSupervisorSignatureDate}{}
\newcommand*{\Xesel@ApproverSignatureDate}{}
\newcommand*{\Xesel@OriginalInventoryNumber}{}
\newcommand*{\Xesel@ReplacedOriginalInventoryNumber}{}
\newcommand*{\Xesel@DuplicateInventoryNumber}{}
\newcommand*{\Xesel@BaseDocumentDesignator}{}
\newcommand*{\Xesel@FirstReferenceDocumentDesignator}{}

% setup data
\newcommand*{\XeselDocumentName} [1]{\renewcommand*{\Xesel@DocumentName}  {#1}}
\newcommand*{\XeselDocumentType} [1]{\renewcommand*{\Xesel@DocumentType}  {#1}}
\newcommand*{\XeselDocumentDesignator} [1]{\renewcommand*{\Xesel@DocumentDesignator}  {#1}}
\newcommand*{\XeselLetterLeft} [1]{\renewcommand*{\Xesel@LetterLeft}  {#1}}
\newcommand*{\XeselLetterMiddle} [1]{\renewcommand*{\Xesel@LetterMiddle}  {#1}}
\newcommand*{\XeselLetterRight} [1]{\renewcommand*{\Xesel@LetterRight}  {#1}}
\newcommand*{\XeselSheetIndex} [1]{\renewcommand*{\Xesel@SheetIndex}  {#1}}
\newcommand*{\XeselSheetsTotal} [1]{\renewcommand*{\Xesel@SheetsTotal}  {#1}}
\newcommand*{\XeselOrganization} [1]{\renewcommand*{\Xesel@Organization}  {#1}}
\newcommand*{\XeselExtraActivityType} [1]{\renewcommand*{\Xesel@ExtraActivityType}  {#1}}
\newcommand*{\XeselDesignerName} [1]{\renewcommand*{\Xesel@DesignerName}  {#1}}
\newcommand*{\XeselCheckerName} [1]{\renewcommand*{\Xesel@CheckerName}  {#1}}
\newcommand*{\XeselExtraActivityName} [1]{\renewcommand*{\Xesel@ExtraActivityName}  {#1}}
\newcommand*{\XeselNormativeSupervisorName} [1]{\renewcommand*{\Xesel@NormativeSupervisorName}  {#1}}
\newcommand*{\XeselApproverName} [1]{\renewcommand*{\Xesel@ApproverName}  {#1}}
\newcommand*{\XeselDesignerSignatureDate} [1]{\renewcommand*{\Xesel@DesignerSignatureDate}  {#1}}
\newcommand*{\XeselCheckerSignatureDate} [1]{\renewcommand*{\Xesel@CheckerSignatureDate}  {#1}}
\newcommand*{\XeselTechnicalSupervisorSignatureDate} [1]{\renewcommand*{\Xesel@TechnicalSupervisorSignatureDate}  {#1}}
\newcommand*{\XeselExtraActivitySignatureDate} [1]{\renewcommand*{\Xesel@ExtraActivitySignatureDate}  {#1}}
\newcommand*{\XeselNormativeSupervisorSignatureDate} [1]{\renewcommand*{\Xesel@NormativeSupervisorSignatureDate}  {#1}}
\newcommand*{\XeselApproverSignatureDate} [1]{\renewcommand*{\Xesel@ApproverSignatureDate}  {#1}}
\newcommand*{\XeselOriginalInventoryNumber} [1]{\renewcommand*{\Xesel@OriginalInventoryNumber}  {#1}}
\newcommand*{\XeselReplacedOriginalInventoryNumber} [1]{\renewcommand*{\Xesel@ReplacedOriginalInventoryNumber}  {#1}}
\newcommand*{\XeselDuplicateInventoryNumber} [1]{\renewcommand*{\Xesel@DuplicateInventoryNumber}  {#1}}
\newcommand*{\XeselBaseDocumentDesignator}[1]{\renewcommand*{\Xesel@BaseDocumentDesignator}{#1}}
\newcommand*{\XeselFirstReferenceDocumentDesignator}[1]{\renewcommand*{\Xesel@FirstReferenceDocumentDesignator}{#1}}
\newcommand*{\Xesel@DocumentNameFull}{{\XeselFontFormDocName\Xesel@DocumentName}\\{\XeselFontFormDocType\Xesel@DocumentType}} %если придёт пустой DocumentName то вылетит - надо фиксить

% entry commands
\newcommand*{\XeselEntry}[4]{#1 & #2 & #3 & #4 \\}
\newcommand*{\XeselHeader}[1]{& \multicolumn{1}{c}{\textbf{#1}} &&\\\nopagebreak}

% draw variables
\newlength{\ELHeight}
\newlength{\ELStampHeight}
\newcounter{ELLines}

% begin drawing
\AtBeginShipout{%
	\AtBeginShipoutUpperLeft{%
		\begin{picture}(0mm,0mm)(0mm,\paperheight)
			%\color{gray}
			% draw border
			\linethickness{0.4mm}
			\put(20mm,5mm)  {\line(1,0){185mm}}
			\put(20mm,292mm){\line(1,0){185mm}}
			\put(20mm,5mm)  {\line(0,1){287mm}}
			\put(205mm,5mm) {\line(0,1){287mm}}
			\ifnum \thepage = 1
				\ELHeight=247mm
				\ELStampHeight=40mm
				\setcounter{ELLines}{28}
			\else
				\ELHeight=272mm
				\ELStampHeight=15mm
				\setcounter{ELLines}{31}
			\fi
			% draw extra fields
			\put(8mm,5mm){\begin{picture}(0mm,0mm) % do NOT split this line, contents will shift to the right otherwise
					%\color{green}
					% vertical lines
					\put(0mm,0mm){\line(0,1){145mm}}
					\put(5mm,0mm){\line(0,1){145mm}}
					% horisontal lines
					\put(0mm,  0mm){\line(1,0){12mm}}
					\put(0mm, 25mm){\line(1,0){12mm}}
					\put(0mm, 60mm){\line(1,0){12mm}}
					\put(0mm, 85mm){\line(1,0){12mm}}
					\put(0mm,110mm){\line(1,0){12mm}}
					\put(0mm,145mm){\line(1,0){12mm}}
					% text
					\put(-1mm,  0.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraHeader Инв. № подл.}\end{sideways}}
					\put(-1mm, 25.5mm){\begin{sideways}\parbox[c][5mm][b]{34mm}{\centering\XeselFormFont\XeselFontExtraHeader Подп. и дата}\end{sideways}}
					\put(-1mm, 60.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraHeader Взам. инв. №}\end{sideways}}
					\put(-1mm, 85.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraHeader Инв. № дубл.}\end{sideways}}
					\put(-1mm,110.5mm){\begin{sideways}\parbox[c][5mm][b]{34mm}{\centering\XeselFormFont\XeselFontExtraHeader Подп. и дата}\end{sideways}}
					\put( 5mm,  0.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraData\Xesel@OriginalInventoryNumber}\end{sideways}}
					\put( 5mm, 60.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraData\Xesel@ReplacedOriginalInventoryNumber}\end{sideways}}
					\put( 5mm, 85.5mm){\begin{sideways}\parbox[c][5mm][b]{24mm}{\centering\XeselFormFont\XeselFontExtraData\Xesel@DuplicateInventoryNumber}\end{sideways}}
					\ifnum \thepage = 1
						% vertical lines
						\put(0mm,167mm){\line(0,1){120mm}}
						\put(5mm,167mm){\line(0,1){120mm}}
						% horisontal lines
						\put(0mm,167mm){\line(1,0){12mm}}
						\put(0mm,227mm){\line(1,0){12mm}}
						\put(0mm,287mm){\line(1,0){12mm}}
						% text
						\put(-1mm,167.5mm){\begin{sideways}\parbox[c][5mm][b]{59mm}{\centering\XeselFormFont\XeselFontExtraHeader Справ. №}\end{sideways}}
						\put(-1mm,227.5mm){\begin{sideways}\parbox[c][5mm][b]{59mm}{\centering\XeselFormFont\XeselFontExtraHeader Перв. примен.}\end{sideways}}
						\put(5mm,167.5mm){\begin{sideways}\parbox[c][5mm][b]{59mm}{\centering\XeselFormFont\XeselFontExtraData\Xesel@BaseDocumentDesignator}\end{sideways}}
						\put(5mm,227.5mm){\begin{sideways}\parbox[c][5mm][b]{59mm}{\centering\XeselFormFont\XeselFontExtraData\Xesel@FirstReferenceDocumentDesignator}\end{sideways}}
					\fi
				\end{picture}
			}%
			% go to inframe drawing
			\put(20mm,5mm){\begin{picture}(0mm,0mm) % do NOT split this line, contents will shift to the right otherwise
					%\color{blue}
					% draw table
					\put(20mm,\ELStampHeight) {\line(0,1){\ELHeight}}
					\put(130mm,\ELStampHeight){\line(0,1){\ELHeight}}
					\put(140mm,\ELStampHeight){\line(0,1){\ELHeight}}
					\put(0mm,272mm){\line(1,0){185mm}}
					\linethickness{0.2mm}
					\multiput(0mm,264mm)(0mm,-8mm){\arabic{ELLines}}{\line(1,0){185mm}}
					\linethickness{0.4mm}
					\put(  0mm,272mm){\parbox[b][15mm][c]{ 20mm}{\centering\XeselFormFont\XeselFontTableHeader Поз. обозначе-ние}}
					\put( 20mm,272mm){\parbox[b][15mm][c]{110mm}{\centering\XeselFormFont\XeselFontTableHeader Наименование}}
					\put(130mm,272mm){\parbox[b][15mm][c]{ 10mm}{\centering\XeselFormFont\XeselFontTableHeader Кол.}}
					\put(140mm,272mm){\parbox[b][15mm][c]{ 45mm}{\centering\XeselFormFont\XeselFontTableHeader Примечание}}
					%
					% draw stamp
					\put(0,\ELStampHeight){\line(1,0){185mm}}
					\ifnum \thepage = 1
						% vertical lines
						\put( 17mm,  0mm){\line(0,1){\ELStampHeight}}
						\put( 40mm,  0mm){\line(0,1){\ELStampHeight}}
						\put( 55mm,  0mm){\line(0,1){\ELStampHeight}}
						\put( 65mm,  0mm){\line(0,1){\ELStampHeight}}
						\put(  7mm, 25mm){\line(0,1){15mm}}
						\put(135mm,  0mm){\line(0,1){25mm}}
						\put(150mm, 15mm){\line(0,1){10mm}}
						\put(165mm, 15mm){\line(0,1){10mm}}
						\linethickness{0.2mm}
						\multiput(140mm, 15mm)(5mm,0mm){2}{\line(0,1){5mm}}
						\linethickness{0.4mm}
						% horisontal lines
						\put(  0mm, 25mm){\line(1,0){185mm}}
						\put(  0mm, 30mm){\line(1,0){65mm}}
						\multiput(135mm, 15mm)(0mm,5mm){2}{\line(1,0){50mm}}
						\linethickness{0.2mm}
						\multiput(0mm, 5mm)(0mm,5mm){4}{\line(1,0){65mm}}
						\put(0mm,35mm){\line(1,0){65mm}}
						\linethickness{0.4mm}
						% text
						\put( 0.5mm, 26mm){\parbox[b][5mm][b]{ 6mm}{\centering\XeselFormFont\XeselFontFormHeader Изм.}}
						\put( 7.5mm, 26mm){\parbox[b][5mm][b]{ 9mm}{\centering\XeselFormFont\XeselFontFormHeader Лист}}
						\put(17.5mm, 26mm){\parbox[b][5mm][b]{22mm}{\centering\XeselFormFont\XeselFontFormHeader №\ докум.}}
						\put(40.5mm, 26mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormHeader Подп.}}
						\put(55.5mm, 26mm){\parbox[b][5mm][b]{ 9mm}{\centering\XeselFormFont\XeselFontFormHeader Дата}}
						%
						\put( 0.5mm, 21mm){\parbox[b][5mm][b]{20mm}{\XeselFormFont\XeselFontFormHeader Разраб.}}
						\put( 0.5mm, 16mm){\parbox[b][5mm][b]{20mm}{\XeselFormFont\XeselFontFormHeader Проверил}}
						\put( 0.5mm, 11mm){\parbox[b][5mm][b]{20mm}{\XeselFormFont\XeselFontFormHeader\Xesel@ExtraActivityType}}
						\put( 0.5mm,  6mm){\parbox[b][5mm][b]{20mm}{\XeselFormFont\XeselFontFormHeader Н. контр.}}
						\put( 0.5mm,  1mm){\parbox[b][5mm][b]{20mm}{\XeselFormFont\XeselFontFormHeader Утв.}}
						%
						\put(17.5mm, 21mm){\parbox[b][5mm][b]{25mm}{\XeselFormFont\XeselFontFormNames\Xesel@DesignerName}}
						\put(17.5mm, 16mm){\parbox[b][5mm][b]{25mm}{\XeselFormFont\XeselFontFormNames\Xesel@CheckerName}}
						\put(17.5mm, 11mm){\parbox[b][5mm][b]{25mm}{\XeselFormFont\XeselFontFormNames\Xesel@ExtraActivityName}}
						\put(17.5mm,  6mm){\parbox[b][5mm][b]{25mm}{\XeselFormFont\XeselFontFormNames\Xesel@NormativeSupervisorName}}
						\put(17.5mm,  1mm){\parbox[b][5mm][b]{25mm}{\XeselFormFont\XeselFontFormNames\Xesel@ApproverName}}
						%
						\put(55.0mm, 21.5mm){\parbox[b][3mm][b]{10mm}{\centering\XeselFormFont\XeselFontFormDates\Xesel@DesignerSignatureDate}}
						\put(55.0mm, 16.5mm){\parbox[b][3mm][b]{10mm}{\centering\XeselFormFont\XeselFontFormDates\Xesel@CheckerSignatureDate}}
						\put(55.0mm, 11.5mm){\parbox[b][3mm][b]{10mm}{\centering\XeselFormFont\XeselFontFormDates\Xesel@ExtraActivitySignatureDate}}
						\put(55.0mm,  6.5mm){\parbox[b][3mm][b]{10mm}{\centering\XeselFormFont\XeselFontFormDates\Xesel@NormativeSupervisorSignatureDate}}
						\put(55.0mm,  1.5mm){\parbox[b][3mm][b]{10mm}{\centering\XeselFormFont\XeselFontFormDates\Xesel@ApproverSignatureDate}}
						%
						\put(135.5mm, 21mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormHeader Лит.}}
						\put(130.0mm, 16mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormLetters\Xesel@LetterLeft}}
						\put(135.0mm, 16mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormLetters\Xesel@LetterMiddle}}
						\put(140.0mm, 16mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormLetters\Xesel@LetterRight}}
						\put(150.5mm, 21mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormHeader Лист}}
						\put(165.5mm, 21mm){\parbox[b][5mm][b]{19mm}{\centering\XeselFormFont\XeselFontFormHeader Листов}}
						%
						\put(150.5mm, 16mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormPages \thepage}}
						\put(165.5mm, 16mm){\parbox[b][5mm][b]{19mm}{\centering\XeselFormFont\XeselFontFormPages \pageref{xesel:\arabic{xesel}:lastpage}} }
						%
						\put(  65mm,  25mm){\parbox[b][15mm][c]{120mm}{\centering\XeselFormFont\XeselFontFormDocDesignator\Xesel@DocumentDesignator}}
						\put(  65mm,   0mm){\parbox[b][25mm][c]{ 70mm}{\centering\XeselFormFont\Xesel@DocumentNameFull}}
						\put( 135mm,   0mm){\parbox[b][15mm][c]{ 50mm}{\centering\XeselFormFont\XeselFontFormOrganization\Xesel@Organization}}
					\else
						% vertical lines
						\put(  7mm, 0mm){\line(0,1){\ELStampHeight}}
						\put( 17mm, 0mm){\line(0,1){\ELStampHeight}}
						\put( 40mm, 0mm){\line(0,1){\ELStampHeight}}
						\put( 55mm, 0mm){\line(0,1){\ELStampHeight}}
						\put( 65mm, 0mm){\line(0,1){\ELStampHeight}}
						\put(175mm, 0mm){\line(0,1){\ELStampHeight}}
						% horisontal lines
						\put(  0mm, 5mm){\line(1,0){65mm}}
						\put(175mm, 8mm){\line(1,0){10mm}}
						\linethickness{0.2mm}
						\put(  0mm,10mm){\line(1,0){65mm}}
						\linethickness{0.4mm}
						% draw text
						\put( 0.5mm, 1mm){\parbox[b][5mm][b]{ 6mm}{\centering\XeselFormFont\XeselFontFormHeader Изм.}                    }
						\put( 7.5mm, 1mm){\parbox[b][5mm][b]{ 9mm}{\centering\XeselFormFont\XeselFontFormHeader Лист}                    }
						\put(17.5mm, 1mm){\parbox[b][5mm][b]{22mm}{\centering\XeselFormFont\XeselFontFormHeader №\ докум.}               }
						\put(40.5mm, 1mm){\parbox[b][5mm][b]{14mm}{\centering\XeselFormFont\XeselFontFormHeader Подп.}                   }
						\put(55.5mm, 1mm){\parbox[b][5mm][b]{ 9mm}{\centering\XeselFormFont\XeselFontFormHeader Дата}                    }
						\put( 175mm, 9mm){\parbox[b][7mm][b]{ 9mm}{\centering\XeselFormFont\XeselFontFormHeader\centering Лист}          }
						\put( 175mm, 0mm){\parbox[b][7mm][c]{ 9mm}{\centering\XeselFormFont\XeselFontFormPages\centering \arabic{page}} }
						% draw number
						\put(  65mm, 0mm){ \parbox[b][15mm][c]{110mm}{\centering\XeselFormFont\XeselFontFormDocDesignator \Xesel@DocumentDesignator}}
					\fi
				\end{picture}
			}%
		\end{picture}
	}%
}%

\pagestyle{empty}
\tabcolsep=1mm
\renewcommand*{\arraystretch}{1.0}
\setlength{\extrarowheight}{0mm}

% xesel environments counter
\newcounter{xesel}
\setcounter{xesel}{0}

% xesel environment
\newenvironment{xesel}{%
\stepcounter{xesel}
\setcounter{page}{1}
\enlargethispage{-24mm}
\XeselDataFont\XeselFontTableData
\begin{longtable}{>{\centering}p{18mm} >{\raggedright}p{108mm} >{\centering}p{8mm} p{43mm}}
	}{
	\label{xesel:\arabic{xesel}:lastpage} % маркировка количества листов на первом листе
\end{longtable}}

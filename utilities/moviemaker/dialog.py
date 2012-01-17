#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys
import time

import cgruconfig
import cgruutils

from PyQt4 import QtCore, QtGui

# Command arguments:

from optparse import OptionParser
Parser = OptionParser(usage="%prog [options] [file]\ntype \"%prog -h\" for help", version="%prog 1.0")
Parser.add_option('-s', '--slate',           dest='slate',           type  ='string',     default='dailies_slate',help='Slate frame template')
Parser.add_option('-t', '--template',        dest='template',        type  ='string',     default='dailies_withlogo', help='Sequence frame template')
Parser.add_option('-c', '--codec',           dest='codec',           type  ='string',     default='photojpg_best.ffmpeg', help='Codec preset')
Parser.add_option('-f', '--format',          dest='format',          type  ='string',     default='720x576x1.09', help='Resolution')
Parser.add_option('-n', '--container',       dest='container',       type  ='string',     default='mov',          help='Container')
Parser.add_option('--aspect_in',             dest='aspect_in',       type  ='float',      default=-1.0,           help='Input image aspect, -1 = no changes')
Parser.add_option('--aspect_auto',           dest='aspect_auto',     type  ='float',      default=-1.0,           help='Auto image aspect (2 if w/h <= aspect_auto), -1 = no changes')
Parser.add_option('--aspect_out',            dest='aspect_out',      type  ='float',      default=-1.0,           help='Output movie aspect, "-1" = no changes')
Parser.add_option('--tmpformat',             dest='tmpformat',       type  ='string',     default='tga',          help='Temporary images format')
Parser.add_option('--tmpquality',            dest='tmpquality',      type  ='string',     default='',             help='Temporary images format quality options')
Parser.add_option('--noidentify',            dest='noidentify',      action='store_true', default=False,          help='Disable image identification')
Parser.add_option('--noautocorr',            dest='noautocorr',      action='store_true', default=False,          help='Disable auto color correction for Cineon and EXR')
Parser.add_option('--correction',            dest='correction',      type  ='string',     default='',             help='Add custom color correction parameters')
Parser.add_option('--stereo',                dest='stereo',          action='store_true', default=False,          help='Stereo mode by default')
Parser.add_option('--fps',                   dest='fps',             type  ='string',     default='25',           help='Frames per second')
Parser.add_option('--company',               dest='company',         type  ='string',     default='',             help='Company name')
Parser.add_option('--project',               dest='project',         type  ='string',     default='',             help='Project name')
Parser.add_option('--artist',                dest='artist',          type  ='string',     default='',             help='Artist name')
Parser.add_option('--naming',                dest='naming',          type  ='string',     default='',             help='Auto movie naming rule: [s]_[v]_[d]')
Parser.add_option('--cacher_aspect',         dest='cacher_aspect',   type  ='float',      default=1.85,           help='Cacher aspect')
Parser.add_option('--cacher_opacity',        dest='cacher_opacity',  type  ='int',        default=0,              help='Cacher opacity')
Parser.add_option('--line_aspect',           dest='line_aspect',     type  ='float',      default=1.85,           help='Cacher line aspect')
Parser.add_option('--line_color',            dest='line_color',      type  ='string',     default='',             help='Cacher line opacity')
Parser.add_option('--draw169',               dest='draw169',         type  ='int',        default=0,              help='Draw 16:9 cacher opacity')
Parser.add_option('--draw235',               dest='draw235',         type  ='int',        default=0,              help='Draw 2.35 cacher opacity')
Parser.add_option('--line169',               dest='line169',         type  ='string',     default='',             help='Draw 16:9 line color: "255,255,0"')
Parser.add_option('--line235',               dest='line235',         type  ='string',     default='',             help='Draw 2.35 line color: "255,255,0"')
Parser.add_option('--fff',                   dest='fffirst',         action='store_true', default=False,          help='Draw first frame as first, and not actual first frame number.')
Parser.add_option('--lgspath',         		dest='lgspath',    		type  ='string',     default='logo.png',     help='Slate logo')
Parser.add_option('--lgssize',         		dest='lgssize',    		type  ='int',        default=25,   	         help='Slate logo size, percent of image')
Parser.add_option('--lgsgrav',         		dest='lgsgrav',    		type  ='string',     default='southeast', 	help='Slate logo positioning gravity')
Parser.add_option('--lgfpath',         		dest='lgfpath',    		type  ='string',     default='logo.png',     help='Frame logo')
Parser.add_option('--lgfsize',         		dest='lgfsize',    		type  ='int',        default=10,   	         help='Frame logo size, percent of image')
Parser.add_option('--lgfgrav',         		dest='lgfgrav',    		type  ='string',     default='north',        help='Frame logo positioning gravity')
Parser.add_option('-A', '--afanasy',         dest='afanasy',         action='store_true', default=False,          help='Send Afanasy job')
Parser.add_option(      '--afpriority',      dest='afpriority',      type  ='int',        default=-1,             help='Afanasy job priority')
Parser.add_option(      '--afmaxhosts',      dest='afmaxhosts',      type  ='int',        default=-1,             help='Afanasy job maximum hosts')
Parser.add_option(      '--afhostsmask',     dest='afhostsmask',     type  ='string',     default='',             help='Afanasy job hosts mask')
Parser.add_option(      '--afhostsmaskex',   dest='afhostsmaskex',   type  ='string',     default='',             help='Afanasy job exclude hosts mask')
Parser.add_option(      '--afdependmask',    dest='afdependmask',    type  ='string',     default='',             help='Afanasy job depend mask')
Parser.add_option(      '--afdependmaskgl',  dest='afdependmaskgl',  type  ='string',     default='',             help='Afanasy job global depend mask')
Parser.add_option(      '--afcapacity',      dest='afcapacity',      type  ='int',        default=-1,             help='Afanasy job tasks capacity')
Parser.add_option(      '--afpause',         dest='afpause',         action='store_true', default=False,          help='Start Afanasy job paused')
Parser.add_option('-D', '--debug',           dest='debug',           action='store_true', default=False,          help='Debug mode')

Parser.add_option(      '--wndicon',         dest='wndicon',         type  ='string',     default='dailies',      help='Set dialog window icon filename.')

(Options, args) = Parser.parse_args()

if len(args) > 2: Parser.error('Too many arguments provided.')

InFile1 = ''
InFile2 = ''

if len(args) > 0: InFile1 = os.path.abspath( args[0])
if len(args) > 1: InFile2 = os.path.abspath( args[1])

# Initializations:
DialogPath = os.path.dirname(os.path.abspath(sys.argv[0]))
TemplatesPath = os.path.join( DialogPath, 'templates')
LogosPath = os.path.join( DialogPath, 'logos')
CodecsPath = os.path.join( DialogPath, 'codecs')
FormatsPath = os.path.join( DialogPath, 'formats')
FPS = ['23.976','24','25','30','48','50']

Activities = ['comp','render','anim','dyn','sim','stereo','cloth','part','skin','setup','clnup','mtpnt','rnd','test']
FontsList = ['','Arial','Courier-New','Impact','Tahoma','Times-New-Roman','Verdana']
Encoders = ['ffmpeg', 'mencoder', 'nuke']
Gravity = ['SouthEast','South','SouthWest','West','NorthWest','North','NorthEast','East','Center']

Namings = [
'(s)_(v)_(d)',
'(S)_(V)_(D)',
'(s)_(a)_(v)_(d)',
'(S)_(A)_(V)_(D)',
'(s)_(v)_(a)_(d)',
'(S)_(V)_(A)_(D)',
'(P)_(S)_(V)_(D)_(A)_(C)_(U)',
'(p)_(s)_(v)_(d)_(a)_(c)_(u)'
]
if Options.naming != '' and not Options.naming in Namings: Namings.append( Options.naming)

AudioCodecNames  = [   'MP3 (Mpeg-1 Layer 3)', 'AAC (Advanced Audio Codec)',     'Vorbis', 'FLAC (Free Lossless Audio Codec)']
AudioCodecValues = [             'libmp3lame',                    'libfaac',  'libvorbis',                             'flac']

# Process Containers:
Containers = ['mov','avi','mp4','m4v']
if not str(Options.container) in Containers: Containers.append( str(Options.container))

# Process Cacher:
CacherNames  = ['None', '25%', '50%', '75%', '100%']
CacherValues = [   '0', '25' , '50' , '75' , '100' ]
if not str(Options.draw169) in CacherValues:
   CacherNames.append(  str(Options.draw169))
   CacherValues.append( str(Options.draw169))
if not str(Options.draw235) in CacherValues:
   CacherNames.append(  str(Options.draw235))
   CacherValues.append( str(Options.draw235))

# Precess Artist:
Artist = Options.artist
if Artist == '': Artist = os.getenv('USER', os.getenv('USERNAME', 'user'))
# cut DOMAIN from username:
dpos = Artist.rfind('/')
if dpos == -1: dpos = Artist.rfind('\\')
if dpos != -1: Artist = Artist[dpos+1:]
Artist = Artist.capitalize()

# Process formats:
FormatNames = []
FormatValues = []
FormatFiles = []
allFiles = os.listdir( FormatsPath)
for afile in allFiles:
   afile = os.path.join( FormatsPath, afile)
   if os.path.isfile( afile): FormatFiles.append( afile)
FormatFiles.sort()
for afile in FormatFiles:
   file = open( afile)
   FormatNames.append(file.readline().strip())
   FormatValues.append(file.readline().strip())
   file.close()
FormatNames.append('Encode "as is" only')
FormatValues.append('')
if not Options.format in FormatValues:
   FormatValues.append( Options.format)
   FormatNames.append( Options.format)

# Process temporary images format:
TmpImgFormats = ['tga','jpg']
if Options.tmpformat not in TmpImgFormats: TmpImgFormats.append( Options.tmpformat)

# Process templates:
Templates = ['']
TemplateF = 0
TemplateS = 0
if os.path.isdir(TemplatesPath):
   files = os.listdir(TemplatesPath)
   files.sort()
   index = 0
   for afile in files:
      if afile[0] == '.': continue
      index += 1
      Templates.append(afile)
      if afile == Options.slate:    TemplateS = index
      if afile == Options.template: TemplateF = index


# Process codecs:
CodecNames = []
CodecFiles = []
allFiles = os.listdir( CodecsPath)
for afile in allFiles:
   afile = os.path.join( CodecsPath, afile)
   if os.path.isfile( afile):
      parts = afile.split('.')
      if len(parts):
         if parts[len(parts)-1] in Encoders:
            CodecFiles.append( afile)
CodecFiles.sort()
for afile in CodecFiles:
   file = open( afile)
   name = file.readline().strip()
   file.close()
   CodecNames.append( name)

class Dialog( QtGui.QWidget):
   def __init__( self):
      QtGui.QWidget.__init__( self)

      self.setWindowTitle('Make Movie - CGRU ' + cgruconfig.VARS['CGRU_VERSION'])

      self.constructed = False
      self.evaluated = False
      self.running   = False
      self.decode    = False

      mainLayout = QtGui.QVBoxLayout( self)
      tabwidget = QtGui.QTabWidget( self)
      mainLayout.addWidget( tabwidget)

      generalwidget = QtGui.QWidget( self)
      tabwidget.addTab( generalwidget,'General')
      generallayout = QtGui.QVBoxLayout( generalwidget)

      drawingwidget = QtGui.QWidget( self)
      tabwidget.addTab( drawingwidget,'Drawing')
      drawinglayout = QtGui.QVBoxLayout( drawingwidget)

      parameterswidget = QtGui.QWidget( self)
      tabwidget.addTab( parameterswidget,'Parameters')
      parameterslayout = QtGui.QVBoxLayout( parameterswidget)

      stereowidget = QtGui.QWidget( self)
      tabwidget.addTab( stereowidget,'Stereo')
      stereolayout = QtGui.QVBoxLayout( stereowidget)

      decodewidget = QtGui.QWidget( self)
      tabwidget.addTab( decodewidget,'Decode')
      decodeLayout = QtGui.QVBoxLayout( decodewidget)

      audiowidget = QtGui.QWidget( self)
      tabwidget.addTab( audiowidget,'Audio')
      audioLayout = QtGui.QVBoxLayout( audiowidget)

      afanasywidget = QtGui.QWidget( self)
      tabwidget.addTab( afanasywidget,'Afanasy')
      afanasylayout = QtGui.QVBoxLayout( afanasywidget)


      # General:
      self.fields = dict()

      # Format:
      layout = QtGui.QHBoxLayout()
      label = QtGui.QLabel('Format:', self)
      label.setToolTip('\
Movie resolution.\n\
Format presets located in\n\
' + FormatsPath)
      layout.addWidget( label)
      self.cbFormat = QtGui.QComboBox( self)
      i = 0
      for format in FormatValues:
         self.cbFormat.addItem( FormatNames[i], format)
         if format == Options.format: self.cbFormat.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbFormat, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      layout.addWidget( self.cbFormat)

      self.tFPS = QtGui.QLabel('FPS:', self)
      self.tFPS.setToolTip('\
Frame rate.')
      self.cbFPS = QtGui.QComboBox( self)
      i = 0
      for fps in FPS:
         self.cbFPS.addItem(fps)
         if fps == Options.fps: self.cbFPS.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbFPS, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      layout.addWidget( self.tFPS)
      layout.addWidget( self.cbFPS)

      tCodec = QtGui.QLabel('Codec:', self)
      tCodec.setToolTip('\
Codec presets located in\n\
' + CodecsPath)
      self.cbCodec = QtGui.QComboBox( self)
      i = 0
      for name in CodecNames:
         self.cbCodec.addItem( name, CodecFiles[i])
         if os.path.basename(CodecFiles[i]) == Options.codec: self.cbCodec.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbCodec, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      layout.addWidget( tCodec)
      layout.addWidget( self.cbCodec)

      tContainer = QtGui.QLabel('Container:')
      layout.addWidget( tContainer)
      self.cbContainer = QtGui.QComboBox( self)
      i = 0
      for cont in Containers:
         self.cbContainer.addItem( cont)
         if cont == Options.container: self.cbContainer.setCurrentIndex(i)
         i += 1
      QtCore.QObject.connect( self.cbContainer, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      layout.addWidget( self.cbContainer)

      generallayout.addLayout( layout)


      gInformation = QtGui.QGroupBox('Information')
      lInformation = QtGui.QVBoxLayout()
      gInformation.setLayout( lInformation)

      lTitles = QtGui.QHBoxLayout()
      tCompany = QtGui.QLabel('Company:', self)
      tCompany.setToolTip('\
Draw company name.\n\
Leave empty to skip.')
      self.editCompany = QtGui.QLineEdit( Options.company, self)
      QtCore.QObject.connect( self.editCompany, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      tProject = QtGui.QLabel('Project:', self)
      tProject.setToolTip('\
Project name.')
      self.editProject = QtGui.QLineEdit( Options.project, self)
      QtCore.QObject.connect( self.editProject, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      tShot = QtGui.QLabel('Shot:', self)
      tShot.setToolTip('\
Shot name.')
      self.editShot = QtGui.QLineEdit('', self)
      QtCore.QObject.connect( self.editShot, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      tVersion = QtGui.QLabel('Version:', self)
      tVersion.setToolTip('\
Shot version.')
      self.editVersion = QtGui.QLineEdit('', self)
      QtCore.QObject.connect( self.editVersion, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cAutoTitles = QtGui.QCheckBox('Auto', self)
      self.cAutoTitles.setToolTip('\
Try to fill values automatically parsing input file name and folder.')
      self.cAutoTitles.setChecked( True)
      QtCore.QObject.connect( self.cAutoTitles, QtCore.SIGNAL('stateChanged(int)'), self.autoTitles)
      lTitles.addWidget( tCompany)
      lTitles.addWidget( self.editCompany)
      lTitles.addWidget( tProject)
      lTitles.addWidget( self.editProject)
      lTitles.addWidget( tShot)
      lTitles.addWidget( self.editShot)
      lTitles.addWidget( tVersion)
      lTitles.addWidget( self.editVersion)
      lTitles.addWidget( self.cAutoTitles)
      lInformation.addLayout( lTitles)

      lUser = QtGui.QHBoxLayout()
      lArtist = QtGui.QLabel('Artist:', self)
      lArtist.setToolTip('\
Artist name.')
      lUser.addWidget( lArtist)
      self.editArtist = QtGui.QLineEdit( Artist, self)
      lUser.addWidget( self.editArtist)
      QtCore.QObject.connect( self.editArtist, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lActivity = QtGui.QLabel('Activity:', self)
      lActivity.setToolTip('\
Shot activity to show.')
      lUser.addWidget( lActivity)
      self.editActivity = QtGui.QLineEdit('', self)
      lUser.addWidget( self.editActivity)
      QtCore.QObject.connect( self.editActivity, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cbActivity = QtGui.QComboBox( self)
      for act in Activities: self.cbActivity.addItem( act)
      lUser.addWidget( self.cbActivity)
      QtCore.QObject.connect( self.cbActivity, QtCore.SIGNAL('currentIndexChanged(int)'), self.activityChanged)
      lInformation.addLayout( lUser)

      lComments = QtGui.QHBoxLayout()
      tComments = QtGui.QLabel('Comments:', self)
      self.editComments = QtGui.QLineEdit( self)
      QtCore.QObject.connect( self.editComments, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lComments.addWidget( tComments)
      lComments.addWidget( self.editComments)
      lInformation.addLayout( lComments)

      generallayout.addWidget( gInformation)

      gInputSettings = QtGui.QGroupBox('Input Sequence Pattern')
      lInputSettings = QtGui.QVBoxLayout()
      gInputSettings.setLayout( lInputSettings)

      self.editInputFiles = QtGui.QLineEdit( InFile1, self)
      self.editInputFiles.setToolTip('\
Input files(s).\n\
You put folder name, file name or files patters here.\n\
Pattern digits can be represented by "%04d" or "####".')
      QtCore.QObject.connect( self.editInputFiles, QtCore.SIGNAL('textEdited(QString)'), self.inputFileChanged)
      lInputSettings.addWidget( self.editInputFiles)

      lBrowseInput = QtGui.QHBoxLayout()
      lFilesCount = QtGui.QLabel('Files count:', self)
      lFilesCount.setToolTip('\
Files founded matching pattern.')
      lBrowseInput.addWidget( lFilesCount)
      self.editInputFilesCount = QtGui.QLineEdit( self)
      self.editInputFilesCount.setEnabled( False)
      lBrowseInput.addWidget( self.editInputFilesCount)
      lPattern = QtGui.QLabel('Pattern:', self)
      lPattern.setToolTip('\
Recognized files pattern.')
      lBrowseInput.addWidget( lPattern)
      self.editInputFilesPattern = QtGui.QLineEdit( self)
      self.editInputFilesPattern.setEnabled( False)
      lBrowseInput.addWidget( self.editInputFilesPattern)

      lFrameRange = QtGui.QLabel('Frames:', self)
      lFrameRange.setToolTip('\
Frame range.')
      lBrowseInput.addWidget( lFrameRange)
      self.sbFrameFirst = QtGui.QSpinBox( self)
      self.sbFrameFirst.setRange( -1, -1)
      QtCore.QObject.connect( self.sbFrameFirst, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lBrowseInput.addWidget( self.sbFrameFirst)
      self.sbFrameLast = QtGui.QSpinBox( self)
      self.sbFrameLast.setRange( -1, -1)
      QtCore.QObject.connect( self.sbFrameLast, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lBrowseInput.addWidget( self.sbFrameLast)
      self.cFFFirst = QtGui.QCheckBox('F.F.First', self)
      self.cFFFirst.setChecked( Options.fffirst)
      self.cFFFirst.setToolTip('\
First Frame First:\n\
Draw first frame number as one.')
      QtCore.QObject.connect( self.cFFFirst, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      lBrowseInput.addWidget( self.cFFFirst)

      self.btnBrowseInput = QtGui.QPushButton('Browse Sequence', self)
      QtCore.QObject.connect( self.btnBrowseInput, QtCore.SIGNAL('pressed()'), self.browseInput)
      lBrowseInput.addWidget( self.btnBrowseInput)
      lInputSettings.addLayout( lBrowseInput)

      lIdentify = QtGui.QHBoxLayout()
      self.cbIdentify = QtGui.QCheckBox('Identify:', self)
      self.cbIdentify.setChecked( not Options.noidentify)
      self.cbIdentify.setToolTip('\
Input file identification.')
      self.editIdentify = QtGui.QLineEdit( self)
      self.editIdentify.setEnabled( False)
      self.btnIdentify = QtGui.QPushButton('Refresh', self)
      QtCore.QObject.connect( self.btnIdentify, QtCore.SIGNAL('pressed()'), self.inputFileChanged)
      lIdentify.addWidget( self.cbIdentify)
      lIdentify.addWidget( self.editIdentify)
      lIdentify.addWidget( self.btnIdentify)
      lInputSettings.addLayout( lIdentify)

      generallayout.addWidget( gInputSettings)


      gOutputSettings = QtGui.QGroupBox('Output File')
      lOutputSettings = QtGui.QVBoxLayout()
      gOutputSettings.setLayout( lOutputSettings)

      lOutputName = QtGui.QHBoxLayout()
      tOutputName = QtGui.QLabel('Name:', self)
      lOutputName.addWidget( tOutputName)
      self.editOutputName = QtGui.QLineEdit( self)
      lOutputName.addWidget( self.editOutputName)
      QtCore.QObject.connect( self.editOutputName, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cAutoOutputName = QtGui.QCheckBox('Rule:', self)
      self.cAutoOutputName.setChecked( True)
      self.cAutoOutputName.setToolTip('\
Use Naming Rule.')
      QtCore.QObject.connect( self.cAutoOutputName, QtCore.SIGNAL('stateChanged(int)'), self.autoOutputName)
      lOutputName.addWidget( self.cAutoOutputName)
      naming = Options.naming
      if naming == '': naming = Namings[0]
      self.editNaming = QtGui.QLineEdit( naming, self)
      QtCore.QObject.connect( self.editNaming, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.editNaming.setMaximumWidth(150)
      lOutputName.addWidget( self.editNaming)
      self.cbNaming = QtGui.QComboBox( self)
      i = 0
      for rule in Namings:
         self.cbNaming.addItem( rule)
         if rule == Options.naming: self.cbNaming.setCurrentIndex( i)
         i += 1
      self.cbNaming.setMaximumWidth(120)
      QtCore.QObject.connect( self.cbNaming, QtCore.SIGNAL('currentIndexChanged(int)'), self.namingChanged)
      lOutputName.addWidget( self.cbNaming)
      lOutputSettings.addLayout( lOutputName)

      lOutputDir = QtGui.QHBoxLayout()
      tOutputDir = QtGui.QLabel('Folder:', self)
      lOutputDir.addWidget( tOutputDir)
      self.editOutputDir = QtGui.QLineEdit( self)
      QtCore.QObject.connect( self.editOutputDir, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lOutputDir.addWidget( self.editOutputDir)
      self.btnBrowseOutputDir = QtGui.QPushButton('Browse', self)
      QtCore.QObject.connect( self.btnBrowseOutputDir, QtCore.SIGNAL('pressed()'), self.browseOutputFolder)
      lOutputDir.addWidget( self.btnBrowseOutputDir)
      lOutputSettings.addLayout( lOutputDir)

      generallayout.addWidget( gOutputSettings)


      # Drawing:

      lTemplates = QtGui.QHBoxLayout()
      tTemplateS = QtGui.QLabel('Slate Template:', self)
      tTemplateS.setToolTip('\
Slate frame template.\n\
Templates are located in\n\
' + TemplatesPath)
      tTemplateF = QtGui.QLabel('Frame Template:', self)
      tTemplateF.setToolTip('\
Frame template.\n\
Templates are located in\n\
' + TemplatesPath)
      self.cbTemplateS = QtGui.QComboBox( self)
      self.cbTemplateF = QtGui.QComboBox( self)
      for template in Templates:
         self.cbTemplateS.addItem(template)
         self.cbTemplateF.addItem(template)
      self.cbTemplateS.setCurrentIndex( TemplateS)
      self.cbTemplateF.setCurrentIndex( TemplateF)
      QtCore.QObject.connect( self.cbTemplateS, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      QtCore.QObject.connect( self.cbTemplateF, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      lTemplates.addWidget( tTemplateS)
      lTemplates.addWidget( self.cbTemplateS)
      lTemplates.addWidget( tTemplateF)
      lTemplates.addWidget( self.cbTemplateF)
      drawinglayout.addLayout( lTemplates)

      self.cTime = QtGui.QCheckBox('Add Time To Date', self)
      self.cTime.setChecked( False)
      QtCore.QObject.connect( self.cTime, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      drawinglayout.addWidget( self.cTime)

      lCacher = QtGui.QHBoxLayout()
      lCacher.addWidget( QtGui.QLabel('Cacher Aspect:', self))
      self.dsbCacherAspect = QtGui.QDoubleSpinBox( self)
      self.dsbCacherAspect.setRange( 0.1, 10.0)
      self.dsbCacherAspect.setDecimals( 6)
      self.dsbCacherAspect.setValue( Options.cacher_aspect)
      QtCore.QObject.connect( self.dsbCacherAspect, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lCacher.addWidget( self.dsbCacherAspect)
      lCacher.addWidget( QtGui.QLabel('Cacher Opacity:', self))
      self.cbCacherOpacity = QtGui.QComboBox( self)
      i = 0
      for cacher in CacherNames:
         self.cbCacherOpacity.addItem( cacher, CacherValues[i])
         if CacherValues[i] == str(Options.cacher_opacity): self.cbCacherOpacity.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbCacherOpacity, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      lCacher.addWidget( self.cbCacherOpacity)
      drawinglayout.addLayout( lCacher)

      lCacherLine = QtGui.QHBoxLayout()
      lCacherLine.addWidget( QtGui.QLabel('Cacher Line Aspect:', self))
      self.dsbCacherLineAspect = QtGui.QDoubleSpinBox( self)
      self.dsbCacherLineAspect.setRange( 0.1, 10.0)
      self.dsbCacherLineAspect.setDecimals( 6)
      self.dsbCacherLineAspect.setValue( Options.line_aspect)
      QtCore.QObject.connect( self.dsbCacherLineAspect, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lCacherLine.addWidget( self.dsbCacherLineAspect)
      tCacherLine = QtGui.QLabel('Cacher Line Color:', self)
      tCacherLine.setToolTip('\
Example "255,255,0" - yellow.')
      lCacherLine.addWidget( tCacherLine)
      self.editCacherLine = QtGui.QLineEdit( Options.line_color, self)
      QtCore.QObject.connect( self.editCacherLine, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lCacherLine.addWidget( self.editCacherLine)
      drawinglayout.addLayout( lCacherLine)

      lCacher169235 = QtGui.QHBoxLayout()
      tCacher169 = QtGui.QLabel('16:9 Cacher:', self)
      self.cbCacher169 = QtGui.QComboBox( self)
      i = 0
      for cacher in CacherNames:
         self.cbCacher169.addItem( cacher, CacherValues[i])
         if CacherValues[i] == str(Options.draw169): self.cbCacher169.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbCacher169, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      tCacher235 = QtGui.QLabel('2.35 Cacher:', self)
      self.cbCacher235 = QtGui.QComboBox( self)
      i = 0
      for cacher in CacherNames:
         self.cbCacher235.addItem( cacher, CacherValues[i])
         if CacherValues[i] == str(Options.draw235): self.cbCacher235.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbCacher235, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      lCacher169235.addWidget( tCacher169)
      lCacher169235.addWidget( self.cbCacher169)
      lCacher169235.addWidget( tCacher235)
      lCacher169235.addWidget( self.cbCacher235)
      drawinglayout.addLayout( lCacher169235)

      lLines = QtGui.QHBoxLayout()
      tLine169 = QtGui.QLabel('Line 16:9 Color:', self)
      tLine169.setToolTip('\
Example "255,255,0" - yellow.')
      lLines.addWidget( tLine169)
      self.editLine169 = QtGui.QLineEdit( Options.line169, self)
      lLines.addWidget( self.editLine169)
      QtCore.QObject.connect( self.editLine169, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      tLine235 = QtGui.QLabel('Line 2.35 Color:', self)
      tLine235.setToolTip('\
Example "255,255,0" - yellow.')
      lLines.addWidget( tLine235)
      self.editLine235 = QtGui.QLineEdit( Options.line235, self)
      lLines.addWidget( self.editLine235)
      QtCore.QObject.connect( self.editLine235, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      drawinglayout.addLayout( lLines)

      # Logos:
      # Slate logo:
      lLgs = QtGui.QHBoxLayout()
      tLgsPath = QtGui.QLabel('Slate Logo:', self)
      lLgs.addWidget( tLgsPath)
      self.editLgsPath = QtGui.QLineEdit( Options.lgspath, self)
      lLgs.addWidget( self.editLgsPath)
      QtCore.QObject.connect( self.editLgsPath, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.btnBrowseLgs = QtGui.QPushButton('Browse', self)
      QtCore.QObject.connect( self.btnBrowseLgs, QtCore.SIGNAL('pressed()'), self.browseLgs)
      lLgs.addWidget( self.btnBrowseLgs)
      self.tLgsSize = QtGui.QLabel('Size:', self)
      lLgs.addWidget( self.tLgsSize)
      self.sbLgsSize = QtGui.QSpinBox( self)
      self.sbLgsSize.setRange( 1, 100)
      self.sbLgsSize.setValue( Options.lgssize)
      QtCore.QObject.connect( self.sbLgsSize, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lLgs.addWidget( self.sbLgsSize)
      tLgsGravity = QtGui.QLabel('%  Position:', self)
      lLgs.addWidget( tLgsGravity)
      self.cbLgsGravity = QtGui.QComboBox( self)
      i = 0
      for grav in Gravity:
         self.cbLgsGravity.addItem( grav)
         if grav.lower() == Options.lgsgrav: self.cbLgsGravity.setCurrentIndex( i)
         i += 1
      lLgs.addWidget( self.cbLgsGravity)
      QtCore.QObject.connect( self.cbLgsGravity, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      drawinglayout.addLayout( lLgs)

      # Frame logo:
      lLgf = QtGui.QHBoxLayout()
      tLgfPath = QtGui.QLabel('Frame Logo:', self)
      lLgf.addWidget( tLgfPath)
      self.editLgfPath = QtGui.QLineEdit( Options.lgfpath, self)
      lLgf.addWidget( self.editLgfPath)
      QtCore.QObject.connect( self.editLgfPath, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.btnBrowseLgf = QtGui.QPushButton('Browse', self)
      QtCore.QObject.connect( self.btnBrowseLgf, QtCore.SIGNAL('pressed()'), self.browseLgf)
      lLgf.addWidget( self.btnBrowseLgf)
      tLgfSize = QtGui.QLabel('Size:', self)
      lLgf.addWidget( tLgfSize)
      self.sbLgfSize = QtGui.QSpinBox( self)
      self.sbLgfSize.setRange( 1, 100)
      self.sbLgfSize.setValue( Options.lgfsize)
      QtCore.QObject.connect( self.sbLgfSize, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lLgf.addWidget( self.sbLgfSize)
      tLgfGravity = QtGui.QLabel('%  Position:', self)
      lLgf.addWidget( tLgfGravity)
      self.cbLgfGravity = QtGui.QComboBox( self)
      i = 0
      for grav in Gravity:
         self.cbLgfGravity.addItem( grav)
         if grav.lower() == Options.lgfgrav: self.cbLgfGravity.setCurrentIndex( i)
         i += 1
      lLgf.addWidget( self.cbLgfGravity)
      QtCore.QObject.connect( self.cbLgfGravity, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      drawinglayout.addLayout( lLgf)

      # Font:
      lFont = QtGui.QHBoxLayout()
      tFont = QtGui.QLabel('Annotations Text Font:', self)
      lFont.addWidget( tFont)
      self.editFont = QtGui.QLineEdit('', self)
      lFont.addWidget( self.editFont)
      QtCore.QObject.connect( self.editFont, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      self.cbFont = QtGui.QComboBox( self)
      for font in FontsList: self.cbFont.addItem( font)
      lFont.addWidget( self.cbFont)
      QtCore.QObject.connect( self.cbFont, QtCore.SIGNAL('currentIndexChanged(int)'), self.fontChanged)
      drawinglayout.addLayout( lFont)


      # Parameters

      # Image Aspect:
      gAspect = QtGui.QGroupBox('Aspect')
      glAspect = QtGui.QVBoxLayout()
      gAspect.setLayout( glAspect)

      lAspectIn = QtGui.QHBoxLayout()
      lAspectIn.addWidget( QtGui.QLabel('Input Images Aspect', self))
      self.dsbAspectIn = QtGui.QDoubleSpinBox( self)
      self.dsbAspectIn.setRange( -1.0, 10.0)
      self.dsbAspectIn.setDecimals( 6)
      self.dsbAspectIn.setValue( Options.aspect_in)
      QtCore.QObject.connect( self.dsbAspectIn, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lAspectIn.addWidget( self.dsbAspectIn)
      lAspectIn.addWidget( QtGui.QLabel(' (-1 = no changes) ', self))
      glAspect.addLayout( lAspectIn)

      lAutoAspect = QtGui.QHBoxLayout()
      tAutoAspect = QtGui.QLabel('Auto Input Aspect', self)
      tAutoAspect.setToolTip('\
Images with width/height ratio > this value will be treated as 2:1.')
      lAutoAspect.addWidget( tAutoAspect)
      self.dsbAutoAspect = QtGui.QDoubleSpinBox( self)
      self.dsbAutoAspect.setRange( -1.0, 10.0)
      self.dsbAutoAspect.setDecimals( 3)
      self.dsbAutoAspect.setValue( Options.aspect_auto)
      QtCore.QObject.connect( self.dsbAutoAspect, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lAutoAspect.addWidget( self.dsbAutoAspect)
      lAutoAspect.addWidget( QtGui.QLabel(' (-1 = no changes) ', self))
      glAspect.addLayout( lAutoAspect)

      lAspectOut = QtGui.QHBoxLayout()
      lAspectOut.addWidget( QtGui.QLabel('Output Movie Aspect', self))
      self.dsbAspectOut = QtGui.QDoubleSpinBox( self)
      self.dsbAspectOut.setRange( -1.0, 10.0)
      self.dsbAspectOut.setDecimals( 6)
      self.dsbAspectOut.setValue( Options.aspect_out)
      QtCore.QObject.connect( self.dsbAspectOut, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lAspectOut.addWidget( self.dsbAspectOut)
      lAspectOut.addWidget( QtGui.QLabel(' (-1 = no changes) ', self))
      glAspect.addLayout( lAspectOut)

      parameterslayout.addWidget( gAspect)

      # Image Correction:
      gCorrectionSettings = QtGui.QGroupBox('Image Correction')
      lCorr = QtGui.QHBoxLayout()
      gCorrectionSettings.setLayout( lCorr)

      self.cCorrAuto = QtGui.QCheckBox('Auto Colorspace', self)
      self.cCorrAuto.setToolTip('\
Automatically convert colors of Linear(EXR) and Cineon(dpx,cin) images to sRGB.')
      self.cCorrAuto.setChecked( not Options.noautocorr)
      QtCore.QObject.connect( self.cCorrAuto, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      lCorr.addWidget( self.cCorrAuto)

      lCorrGamma = QtGui.QHBoxLayout()
      tCorrGamma = QtGui.QLabel('Gamma:', self)
      self.dsbCorrGamma = QtGui.QDoubleSpinBox( self)
      self.dsbCorrGamma.setRange( 0.1, 10.0)
      self.dsbCorrGamma.setDecimals( 1)
      self.dsbCorrGamma.setSingleStep( 0.1)
      self.dsbCorrGamma.setValue( 1.0)
      QtCore.QObject.connect( self.dsbCorrGamma, QtCore.SIGNAL('valueChanged(double)'), self.evaluate)
      lCorrGamma.addWidget( tCorrGamma)
      lCorrGamma.addWidget( self.dsbCorrGamma)
      lCorr.addLayout( lCorrGamma)

      lCorrAux = QtGui.QHBoxLayout()
      tCorrAux = QtGui.QLabel('Custom Options:', self)
      tCorrAux.setToolTip('\
Add this options to convert command.')
      self.eCorrAux = QtGui.QLineEdit( Options.correction, self)
      QtCore.QObject.connect( self.eCorrAux, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lCorrAux.addWidget( tCorrAux)
      lCorrAux.addWidget( self.eCorrAux)
      lCorr.addLayout( lCorrAux)

      parameterslayout.addWidget( gCorrectionSettings)


      # Temporary format options:
      gTempFormat = QtGui.QGroupBox('Intermediate Images')
      lTempFormat = QtGui.QHBoxLayout()
      gTempFormat.setLayout( lTempFormat)

      tTempFormat = QtGui.QLabel('Format:', self)
      self.cbTempFormat = QtGui.QComboBox( self)
      i = 0
      for format in TmpImgFormats:
         self.cbTempFormat.addItem( format)
         if format == Options.tmpformat: self.cbTempFormat.setCurrentIndex( i)
         i += 1
      QtCore.QObject.connect( self.cbTempFormat, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)
      lTempFormat.addWidget( tTempFormat)
      lTempFormat.addWidget( self.cbTempFormat)

      tTempFormatOptions = QtGui.QLabel('Quality Options:', self)
      tTempFormatOptions.setToolTip('\
Add this options to temporary image saving.')
      self.eTempFormatOptions = QtGui.QLineEdit( Options.tmpquality, self)
      QtCore.QObject.connect( self.eTempFormatOptions, QtCore.SIGNAL('editingFinished()'), self.evaluate)
      lTempFormat.addWidget( tTempFormatOptions)
      lTempFormat.addWidget( self.eTempFormatOptions)

      parameterslayout.addWidget( gTempFormat)


      # Auto append output filename:
      dateTimeLayout = QtGui.QHBoxLayout()
      self.cDateOutput = QtGui.QCheckBox('Append Movie File Name With Date', self)
      self.cDateOutput.setChecked( False)
      dateTimeLayout.addWidget( self.cDateOutput)
      QtCore.QObject.connect( self.cDateOutput, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.cTimeOutput = QtGui.QCheckBox('Append Movie File Name With Time', self)
      self.cTimeOutput.setChecked( False)
      dateTimeLayout.addWidget( self.cTimeOutput)
      parameterslayout.addLayout( dateTimeLayout)
      QtCore.QObject.connect( self.cTimeOutput, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)


      # Stereo:

      self.cStereoDuplicate = QtGui.QCheckBox('Duplicate first sequence', self)
      self.cStereoDuplicate.setChecked( Options.stereo)
      QtCore.QObject.connect( self.cStereoDuplicate, QtCore.SIGNAL('stateChanged(int)'), self.evalStereo)
      stereolayout.addWidget( self.cStereoDuplicate)

      # Second Pattern:
      gInputFileGroup2 = QtGui.QGroupBox('Second Sequence Pattern')
      stereolayout.addWidget( gInputFileGroup2)
      lInputFileGroup2 = QtGui.QVBoxLayout()
      gInputFileGroup2.setLayout( lInputFileGroup2)

      self.editInputFiles2 = QtGui.QLineEdit( InFile2, self)
      lInputFileGroup2.addWidget( self.editInputFiles2)
      QtCore.QObject.connect( self.editInputFiles2, QtCore.SIGNAL('textEdited(QString)'), self.inputFileChanged2)

      self.leditInputFileCtrl2 = QtGui.QHBoxLayout()
      self.btnInputFileCopy = QtGui.QPushButton('Copy&&Paste First Sequence', self)
      self.leditInputFileCtrl2.addWidget( self.btnInputFileCopy)
      QtCore.QObject.connect( self.btnInputFileCopy, QtCore.SIGNAL('pressed()'), self.copyInput)
      self.leditInputFileCtrl2.addWidget( QtGui.QLabel('Files count:', self))
      self.editInputFilesCount2 = QtGui.QLineEdit( self)
      self.leditInputFileCtrl2.addWidget( self.editInputFilesCount2)
      self.editInputFilesCount2.setEnabled( False)
      self.leditInputFileCtrl2.addWidget( QtGui.QLabel('Pattern:', self))
      self.editInputFilesPattern2 = QtGui.QLineEdit( self)
      self.leditInputFileCtrl2.addWidget( self.editInputFilesPattern2)
      self.editInputFilesPattern2.setEnabled( False)
      self.btnInputFileBrowse2 = QtGui.QPushButton('Browse', self)
      self.leditInputFileCtrl2.addWidget( self.btnInputFileBrowse2)
      QtCore.QObject.connect( self.btnInputFileBrowse2, QtCore.SIGNAL('pressed()'), self.browseInput2)
      lInputFileGroup2.addLayout( self.leditInputFileCtrl2)

      lIdentify2 = QtGui.QHBoxLayout()
      lIdentify2.addWidget( QtGui.QLabel('Identify:', self))
      self.editIdentify2 = QtGui.QLineEdit( self)
      self.editIdentify2.setEnabled( False)
      lIdentify2.addWidget( self.editIdentify2)
      self.btnInputFileRefresh2 = QtGui.QPushButton('Refresh', self)
      lIdentify2.addWidget( self.btnInputFileRefresh2)
      QtCore.QObject.connect( self.btnInputFileRefresh2, QtCore.SIGNAL('pressed()'), self.inputFileChanged2)
      lInputFileGroup2.addLayout( lIdentify2)

      lStereoStatus = QtGui.QHBoxLayout()
      stereolayout.addLayout( lStereoStatus)
      self.stereoStatusLabel = QtGui.QLabel( 'Stereo Status:', self)
      self.stereoStatusLabel.setAutoFillBackground( True)
      lStereoStatus.addWidget( self.stereoStatusLabel)
      self.editStereoStatus = QtGui.QLineEdit( self)
      lStereoStatus.addWidget( self.editStereoStatus)
      self.editStereoStatus.setReadOnly( True)


      # Decode:
      self.decodeEnable = QtGui.QCheckBox('Enable', self)
      decodeLayout.addWidget( self.decodeEnable)
      QtCore.QObject.connect( self.decodeEnable, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      self.decodeEnable.setChecked( True)
      decodeInputGroup = QtGui.QGroupBox('Input Movie')
      decodeLayout.addWidget( decodeInputGroup)
      decodeInputLayout = QtGui.QVBoxLayout( decodeInputGroup)
      decodeInputFileNameLayout = QtGui.QHBoxLayout()
      decodeInputLayout.addLayout( decodeInputFileNameLayout)
      self.decodeInputFileName = QtGui.QLineEdit( self)
      decodeInputFileNameLayout.addWidget( self.decodeInputFileName)
      QtCore.QObject.connect( self.decodeInputFileName, QtCore.SIGNAL('textEdited(QString)'), self.decodeInputChanged)
      self.decodeInputBrowse = QtGui.QPushButton('Browse')
      decodeInputFileNameLayout.addWidget( self.decodeInputBrowse)
      QtCore.QObject.connect( self.decodeInputBrowse, QtCore.SIGNAL('pressed()'), self.decodeBrowseInput)

      decodeOutputGroup = QtGui.QGroupBox('Output Sequence')
      decodeLayout.addWidget( decodeOutputGroup)
      decodeOutputLayout = QtGui.QVBoxLayout( decodeOutputGroup)
      decodeOutputSequenceLayout = QtGui.QHBoxLayout()
      decodeOutputLayout.addLayout( decodeOutputSequenceLayout)
      self.decodeOutputSequence = QtGui.QLineEdit( self)
      decodeOutputSequenceLayout.addWidget( self.decodeOutputSequence)
      QtCore.QObject.connect( self.decodeOutputSequence, QtCore.SIGNAL('textEdited(QString)'), self.decodeOutputChanged)
      self.decodeOutputBrowse = QtGui.QPushButton('Browse')
      decodeOutputSequenceLayout.addWidget( self.decodeOutputBrowse)
      QtCore.QObject.connect( self.decodeOutputBrowse, QtCore.SIGNAL('pressed()'), self.decodeBrowseOutput)
      decodeOutputLayout.addWidget( QtGui.QLabel('Absolute Location:'))
      self.decodeOutputAbs = QtGui.QLineEdit( self)
      self.decodeOutputAbs.setReadOnly( True)
      decodeOutputLayout.addWidget( self.decodeOutputAbs)
      self.decodeEncode = QtGui.QCheckBox('Encode This Sequence', self)
      decodeOutputLayout.addWidget( self.decodeEncode)
      self.decodeEncode.setChecked( True)


      # Audio:
      audioInputGroup = QtGui.QGroupBox('Input Movie/Sound File')
      audioLayout.addWidget( audioInputGroup)
      audioInputLayout = QtGui.QVBoxLayout( audioInputGroup)
      audioInputFileNameLayout = QtGui.QHBoxLayout()
      audioInputLayout.addLayout( audioInputFileNameLayout)
      self.audioInputFileName = QtGui.QLineEdit( self)
      audioInputFileNameLayout.addWidget( self.audioInputFileName)
      QtCore.QObject.connect( self.audioInputFileName, QtCore.SIGNAL('textEdited(QString)'), self.audioInputChanged)
      self.audioInputBrowse = QtGui.QPushButton('Browse')
      audioInputFileNameLayout.addWidget( self.audioInputBrowse)
      QtCore.QObject.connect( self.audioInputBrowse, QtCore.SIGNAL('pressed()'), self.audioBrowseInput)
      audioSettingsGroup = QtGui.QGroupBox('Settings')
      audioLayout.addWidget( audioSettingsGroup)
      audioSettingsLayout = QtGui.QVBoxLayout( audioSettingsGroup)
      audioFreqLayout = QtGui.QHBoxLayout()
      audioSettingsLayout.addLayout( audioFreqLayout)
      audioFreqLayout.addWidget( QtGui.QLabel('Sampling Frequency:'))
      self.audioFreqSB = QtGui.QSpinBox( self)
      audioFreqLayout.addWidget( self.audioFreqSB)
      self.audioFreqSB.setRange( 1, 96)
      self.audioFreqSB.setValue( 22)
      audioFreqLayout.addWidget( QtGui.QLabel('kHz'))
      QtCore.QObject.connect( self.audioFreqSB, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      audioBitRateLayout = QtGui.QHBoxLayout()
      audioSettingsLayout.addLayout( audioBitRateLayout)
      audioBitRateLayout.addWidget( QtGui.QLabel('Bit Rate:'))
      self.audioBitRateSB = QtGui.QSpinBox( self)
      audioBitRateLayout.addWidget( self.audioBitRateSB)
      self.audioBitRateSB.setRange( 32, 256)
      self.audioBitRateSB.setValue( 128)
      audioBitRateLayout.addWidget( QtGui.QLabel('kB/s'))
      QtCore.QObject.connect( self.audioBitRateSB, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      audioCodecLayout = QtGui.QHBoxLayout()
      audioSettingsLayout.addLayout( audioCodecLayout)
      audioCodecLayout.addWidget( QtGui.QLabel('Codec:'))
      self.audioCodecCB = QtGui.QComboBox( self)
      audioCodecLayout.addWidget( self.audioCodecCB)
      i = 0
      for acodec in AudioCodecNames:
         self.audioCodecCB.addItem( acodec, AudioCodecValues[i])
         i += 1
      self.audioCodecCB.setCurrentIndex( 0)
      QtCore.QObject.connect( self.audioCodecCB, QtCore.SIGNAL('currentIndexChanged(int)'), self.evaluate)



      # Afanasy:

      self.cAfanasy = QtGui.QCheckBox('Enable', self)
      self.cAfanasy.setChecked( Options.afanasy)
      QtCore.QObject.connect( self.cAfanasy, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      afanasylayout.addWidget( self.cAfanasy)

      # Priority
      lAfPriority = QtGui.QHBoxLayout()
      lAfPriority.addWidget( QtGui.QLabel('Priority:', self))
      self.sbAfPriority = QtGui.QSpinBox( self)
      self.sbAfPriority.setRange( -1, 1000000)
      self.sbAfPriority.setValue( Options.afpriority)
      QtCore.QObject.connect( self.sbAfPriority, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfPriority.addWidget( self.sbAfPriority)
      lAfPriority.addWidget( QtGui.QLabel('"-1" Means default value.', self))
      afanasylayout.addLayout( lAfPriority)

      # Hosts
      gAfHosts = QtGui.QGroupBox('Hosts')
      afanasylayout.addWidget( gAfHosts)
      lAfHosts = QtGui.QVBoxLayout()
      gAfHosts.setLayout( lAfHosts)

      lAfMaxHosts = QtGui.QHBoxLayout()
      lAfHosts.addLayout( lAfMaxHosts)
      lAfMaxHosts.addWidget( QtGui.QLabel('Maximum Number:', self))
      self.sbAfMaxHosts = QtGui.QSpinBox( self)
      self.sbAfMaxHosts.setRange( -1, 1000000)
      self.sbAfMaxHosts.setValue( Options.afmaxhosts)
      QtCore.QObject.connect( self.sbAfMaxHosts, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfMaxHosts.addWidget( self.sbAfMaxHosts)
      lAfMaxHosts.addWidget( QtGui.QLabel('"-1" Means no hosts count limit.', self))

      lAfHostsMask = QtGui.QHBoxLayout()
      lAfHosts.addLayout( lAfHostsMask)
      lAfHostsMask.addWidget( QtGui.QLabel('Hosts Names Mask:', self))
      self.editAfHostsMask = QtGui.QLineEdit( Options.afhostsmask, self)
      QtCore.QObject.connect( self.editAfHostsMask, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfHostsMask.addWidget( self.editAfHostsMask)
      lAfHostsMask.addWidget( QtGui.QLabel('Leave empty to run on any host.', self))

      lAfHostsMaskExclude = QtGui.QHBoxLayout()
      lAfHosts.addLayout( lAfHostsMaskExclude)
      lAfHostsMaskExclude.addWidget( QtGui.QLabel('Exclude Hosts Names Mask:', self))
      self.editAfHostsMaskExclude = QtGui.QLineEdit( Options.afhostsmaskex, self)
      QtCore.QObject.connect( self.editAfHostsMaskExclude, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfHostsMaskExclude.addWidget( self.editAfHostsMaskExclude)
      lAfHostsMaskExclude.addWidget( QtGui.QLabel('Leave empty not to exclude any host.', self))

      # Depends
      self.gAfDepends = QtGui.QGroupBox('Depends')
      afanasylayout.addWidget( self.gAfDepends)
      self.lAfDepends = QtGui.QVBoxLayout()
      self.gAfDepends.setLayout( self.lAfDepends)

      self.lAfDependMask = QtGui.QHBoxLayout()
      self.lAfDepends.addLayout( self.lAfDependMask)
      self.tAfDependMask = QtGui.QLabel('Depend Jobs Mask:', self)
      self.lAfDependMask.addWidget( self.tAfDependMask)
      self.editAfDependMask = QtGui.QLineEdit( Options.afdependmask, self)
      QtCore.QObject.connect( self.editAfDependMask, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfDependMask.addWidget( self.editAfDependMask)
      self.tAfDependMaskDef = QtGui.QLabel('Leave empty not to wait any jobs.', self)
      self.lAfDependMask.addWidget( self.tAfDependMaskDef)

      self.lAfDependMaskGlobal = QtGui.QHBoxLayout()
      self.lAfDepends.addLayout( self.lAfDependMaskGlobal)
      self.tAfDependMaskGlobal = QtGui.QLabel('Global Depend Jobs Mask:', self)
      self.lAfDependMaskGlobal.addWidget( self.tAfDependMaskGlobal)
      self.editAfDependMaskGlobal = QtGui.QLineEdit( Options.afdependmaskgl, self)
      QtCore.QObject.connect( self.editAfDependMaskGlobal, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      self.lAfDependMaskGlobal.addWidget( self.editAfDependMaskGlobal)
      self.tAfDependMaskGlobalDef = QtGui.QLabel('Set mask to wait any user jobs.', self)
      self.lAfDependMaskGlobal.addWidget( self.tAfDependMaskGlobalDef)

      # Capacity
      gAfCapacity = QtGui.QGroupBox('Capacity')
      lAfCapacity = QtGui.QHBoxLayout()
      gAfCapacity.setLayout( lAfCapacity)

      self.cAfOneTask = QtGui.QCheckBox('One Task', self)
      self.cAfOneTask.setChecked( True)
      QtCore.QObject.connect( self.cAfOneTask, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      lAfCapacity.addWidget( self.cAfOneTask)

      lAfCapacity.addWidget( QtGui.QLabel('Capacity:', self))
      self.sbAfCapacity = QtGui.QSpinBox( self)
      self.sbAfCapacity.setRange( -1, 1000000)
      self.sbAfCapacity.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapacity, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfCapacity.addWidget( self.sbAfCapacity)

      lAfCapacity.addWidget( QtGui.QLabel('Convert:', self))
      self.sbAfCapConvert = QtGui.QSpinBox( self)
      self.sbAfCapConvert.setRange( -1, 1000000)
      self.sbAfCapConvert.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapConvert, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfCapacity.addWidget( self.sbAfCapConvert)

      lAfCapacity.addWidget( QtGui.QLabel('Encode:', self))
      self.sbAfCapEncode = QtGui.QSpinBox( self)
      self.sbAfCapEncode.setRange( -1, 1000000)
      self.sbAfCapEncode.setValue( Options.afcapacity)
      QtCore.QObject.connect( self.sbAfCapEncode, QtCore.SIGNAL('valueChanged(int)'), self.evaluate)
      lAfCapacity.addWidget( self.sbAfCapEncode)

      afanasylayout.addWidget( gAfCapacity)

      # Pause
      lAfPause = QtGui.QHBoxLayout()
      afanasylayout.addLayout( lAfPause)

      self.cAfPause = QtGui.QCheckBox('Start Job Paused', self)
      self.cAfPause.setChecked( Options.afpause)
      QtCore.QObject.connect( self.cAfPause, QtCore.SIGNAL('stateChanged(int)'), self.evaluate)
      lAfPause.addWidget( self.cAfPause)

      lAfPause.addWidget( QtGui.QLabel('Start At Time:', self))
      self.editAfTime = QtGui.QDateTimeEdit( QtCore.QDateTime.currentDateTime(), self)
      self.editAfTime.setDisplayFormat('dddd d MMMM yyyy, h:mm')
      QtCore.QObject.connect( self.editAfTime, QtCore.SIGNAL('dateTimeChanged()'), self.evaluate)
      lAfPause.addWidget( self.editAfTime)


      # Output Field:

      self.cmdField = QtGui.QTextEdit( self)
      mainLayout.addWidget( self.cmdField)


      # Main Buttons:

      lProcess = QtGui.QHBoxLayout()
      self.btnRefresh = QtGui.QPushButton('Refresh', self)
      QtCore.QObject.connect( self.btnRefresh, QtCore.SIGNAL('pressed()'), self.evaluate)
      self.btnStart = QtGui.QPushButton('Start', self)
      self.btnStart.setEnabled( False)
      QtCore.QObject.connect( self.btnStart, QtCore.SIGNAL('pressed()'), self.execute)
      self.btnStop = QtGui.QPushButton('Stop', self)
      self.btnStop.setEnabled( False)
      QtCore.QObject.connect( self.btnStop, QtCore.SIGNAL('pressed()'), self.processStop)
      lProcess.addWidget( self.btnRefresh)
      lProcess.addWidget( self.btnStart)
      lProcess.addWidget( self.btnStop)
      mainLayout.addLayout( lProcess)


      self.constructed = True
      self.inputPattern = None
      self.inputPattern2 = None
      self.autoTitles()
      self.activityChanged()
      self.autoOutputName()
      self.inputFileChanged()
      self.inputFileChanged2()
      self.evaluate()


# Decode:

   def decodeBrowseInput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a movie file', self.decodeInputFileName.text())
      if len( afile):
         self.decodeInputFileName.setText( afile)
         self.decodeInputChanged()
   def decodeBrowseOutput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a sequence', self.decodeOutputSequence.text())
      if len( afile):
         self.decodeOutputSequence.setText( afile)
         self.decodeOutputChanged()
   def decodeInputChanged( self):
      afile = "%s" % self.decodeInputFileName.text()
      if len( afile):
         pos = afile.rfind('file://')
         if pos >= 0: afile = afile[ pos+7 : ]
         afile = afile.strip()
         afile = afile.strip('\n')
         self.decodeInputFileName.setText( afile)
         self.decodeOutputSequence.setText( os.path.join(os.path.basename( afile) + '-png', os.path.basename( afile) + '.%07d.png'))
         self.decodeEvaluate()
   def decodeOutputChanged( self): self.decodeEvaluate()
   def decodeEvaluate( self):
      if not self.decodeEnable.isChecked(): return False
      self.evaluated = False
      self.btnStart.setEnabled( False)
      if self.running: return False
      self.cmdField.clear()

      inputMovie = "%s" % self.decodeInputFileName.text()
      if len( inputMovie) == 0:
         self.cmdField.setText('Specify input movie to explode into sequence.')
         return False
      inputMovie = os.path.normpath( os.path.abspath( inputMovie))
      if not os.path.isfile( inputMovie):
         self.cmdField.setText('Movie file to decode does not exist.')
         return False
      outputSequence = "%s" % self.decodeOutputSequence.text()
      if len( outputSequence) == 0:
         self.cmdField.setText('Specify output sequence to explode input movie into.')
         return False
      outputSequence = os.path.normpath( os.path.join( os.path.dirname( inputMovie), outputSequence))
      self.decodeOutputAbs.setText( outputSequence)

      cmd = os.environ['CGRU_LOCATION'] + '/utilities/moviemaker/mov2seq.py'
      cmd = os.path.normpath( cmd)
      cmd = 'python "%s"' % cmd
      cmd = cmd + (' "%s" "%s"' % (inputMovie, outputSequence))

      self.cmdField.setText( cmd)
      self.evaluated = True
      self.btnStart.setEnabled( True)
      self.decode = True
      return True


# Encode:

   def audioBrowseInput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose an audio or movie file with sound', self.audioInputFileName.text())
      if len( afile):
         self.audioInputFileName.setText( afile)
         self.audioInputChanged()

   def audioInputChanged( self):
      afile = '%s' % self.audioInputFileName.text()
      if len( afile):
         pos = afile.rfind('file://')
         if pos >= 0:
            afile = afile[ pos+7 : ]
            afile = afile.strip()
            afile = afile.strip('\n')
            self.audioInputFileName.setText( afile)
         self.evaluate()

   def evalStereo( self):
      if self.running: return
      if self.inputPattern2 is None:
         self.cStereoDuplicate.setEnabled( True)
         if self.cStereoDuplicate.isChecked():
            self.editStereoStatus.setText('Stereo from one sequence.')
            self.stereoStatusLabel.setBackgroundRole( QtGui.QPalette.Dark)
         else:
            self.editStereoStatus.setText('No stereo. Specify second sequence or enable duplicate one sequence.')
            self.stereoStatusLabel.setAutoFillBackground( True)
            self.stereoStatusLabel.setBackgroundRole( QtGui.QPalette.Window)
      else:
         self.cStereoDuplicate.setChecked( False)
         self.cStereoDuplicate.setEnabled( False)
         if self.editInputFilesCount.text() == self.editInputFilesCount2.text():
            self.editStereoStatus.setText('Stereo from two sequences.')
            self.stereoStatusLabel.setBackgroundRole( QtGui.QPalette.LinkVisited)
         else:
            self.inputPattern2 = None
            self.editStereoStatus.setText('Two sequences must be the same length.')
            self.evaluated = False
            self.btnStart.setEnabled( False)
            self.cmdField.setText('Sequences length mismatch.')
            return
      if self.inputPattern is not None:
         self.evaluate()

   def copyInput( self):
      files1 = self.editInputFiles.text()
      if len( files1):
         self.editInputFiles2.setText( files1)
      self.inputFileChanged2()

   def autoOutputName( self):
      enable = not self.cAutoOutputName.isChecked()
      self.editOutputName.setEnabled( enable)
      self.cbNaming.setEnabled( not enable)
      self.editNaming.setEnabled( not enable)
      self.evaluate()

   def autoTitles( self):
      enable = not self.cAutoTitles.isChecked()
      self.editProject.setEnabled( enable)
      self.editShot.setEnabled( enable)
      self.editVersion.setEnabled( enable)

   def activityChanged( self):
      self.editActivity.setText( self.cbActivity.currentText())
      self.evaluate()

   def namingChanged( self):
      self.editNaming.setText( self.cbNaming.currentText())
      self.evaluate()

   def fontChanged( self):
      self.editFont.setText( self.cbFont.currentText())
      self.evaluate()

   def browseLgs( self):
      lgspath = LogosPath
      oldlogo = '%s' % self.editLgsPath.text()
      if oldlogo != '':
         dirname = os.path.dirname( oldlogo)
         if dirname != '': lgspath = dirname
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', lgspath)
      if len( afile):
         self.editLgsPath.setText( '%s' % afile)
         self.evaluate()

   def browseLgf( self):
      lgfpath = LogosPath
      oldlogo = '%s' % self.editLgfPath.text()
      if oldlogo != '':
         dirname = os.path.dirname( oldlogo)
         if dirname != '': lgfpath = dirname
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', lgfpath)
      if len( afile):
         self.editLgfPath.setText( '%s' % afile)
         self.evaluate()

   def browseOutputFolder( self):
      folder = QtGui.QFileDialog.getExistingDirectory( self,'Choose a directory', os.path.dirname('%s' % self.editOutputDir.text()))
      if len( folder): self.editOutputDir.setText( folder)

   def browseInput( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', self.editInputFiles.text())
      if len( afile):
         self.editInputFiles.setText( afile)
         self.inputFileChanged()

   def browseInput2( self):
      afile = QtGui.QFileDialog.getOpenFileName( self,'Choose a file', self.editInputFiles2.text())
      if len( afile):
         self.editInputFiles2.setText( afile)
         self.inputFileChanged2()

   def inputFileChanged( self):
      if self.running: return
      self.editInputFilesCount.clear()
      self.editInputFilesPattern.clear()
      self.editIdentify.clear()
      inputfile = '%s' % self.editInputFiles.text()
      InputFile, InputPattern, FilesCount, Identify = self.calcPattern( inputfile)

      self.inputPattern = InputPattern
      if InputPattern == None: return

      self.editInputFiles.setText( InputFile)
      self.editInputFilesPattern.setText( os.path.basename( InputPattern))
      self.editInputFilesCount.setText( '%d' % FilesCount)
      self.editIdentify.setText( Identify)

      self.evaluate()

   def inputFileChanged2( self):
      if self.running: return
      self.editInputFilesCount2.clear()
      self.editInputFilesPattern2.clear()
      self.editIdentify2.clear()
      inputfile = '%s' % self.editInputFiles2.text()
      InputFile, InputPattern, FilesCount, Identify = self.calcPattern( inputfile)

      self.inputPattern2 = InputPattern
      if InputPattern is not None:
         self.editInputFiles2.setText( InputFile)
         self.editInputFilesPattern2.setText( os.path.basename( InputPattern))
         self.editInputFilesCount2.setText( '%d' % FilesCount)
         self.editIdentify2.setText( Identify)
      self.evalStereo()

   def calcPattern( self, InputFile):
      self.evaluated = False
      self.btnStart.setEnabled( False)

      InputPattern = None
      FilesCount = 0
      Identify = ''
      if sys.platform.find('win') == 0: InputFile = InputFile.replace('/','\\')

      if len(InputFile) == 0:
         self.cmdField.setText('Choose one file from sequence.')
         return InputFile, InputPattern, FilesCount, Identify

      # Remove link and strip filename:
      pos = InputFile.rfind('file://')
      if pos >= 0: InputFile = InputFile[ pos+7 : ]
      InputFile = InputFile.strip()
      InputFile = InputFile.strip('\n')

      # If directory is specified, use the first file in it:
      if os.path.isdir( InputFile):
         dirfiles = os.listdir( InputFile)
         if len( dirfiles) == 0:
            print('Folder "%s" is empty.' % InputFile)
            return InputFile, InputPattern, FilesCount, Identify
         InputFile = os.path.join( InputFile, dirfiles[0])

      inputdir = os.path.dirname( InputFile)
      if not os.path.isdir( inputdir):
         self.cmdField.setText('Can\'t find input directory.')
         return InputFile, InputPattern, FilesCount, Identify
      filename = os.path.basename( InputFile)

      # Search %04d pattern:
      digitsall = re.findall(r'%0\dd', filename)
      if len(digitsall):
         padstr = digitsall[-1]
         padding = int( padstr[2])
         pos = filename.rfind( padstr)
         prefix = filename[ : pos]
         suffix = filename[pos+4 : ]
      else:
         # Search %d pattern:
         digitsall = re.findall(r'%d', filename)
         if len(digitsall):
            padstr = digitsall[-1]
            padding = -1
            pos = filename.rfind( padstr)
            prefix = filename[ : pos]
            suffix = filename[pos+2 : ]
         else:
            # Search #### pattern:
            digitsall = re.findall(r'(#{1,})', filename)
            if len(digitsall) == 0:
               # Search digits pattern:
               digitsall = re.findall(r'([0-9]{1,})', filename)
            if len(digitsall):
               digits = digitsall[-1]
               pos = filename.rfind(digits)
               prefix = filename[ : pos]
               padding = len(digits)
               suffix = filename[pos+padding : ]
               padstr = ''
               for d in range(padding): padstr += '#'
            else:
               self.cmdField.setText('Can\'t find digits in input file name.')
               return InputFile, InputPattern, FilesCount, Identify

      pattern = prefix + padstr + suffix

      if padding > 1:
         expr = re.compile( r'%(prefix)s([0-9]{%(padding)d,%(padding)d})%(suffix)s' % vars())
      else:
         expr = re.compile( r'%(prefix)s([0-9]{1,})%(suffix)s' % vars())
      FilesCount = 0
      framefirst = -1
      framelast  = -1
      prefixlen = len(prefix)
      suffixlen = len(suffix)
      allItems = os.listdir( inputdir)
      for item in allItems:
         if not os.path.isfile( os.path.join( inputdir, item)): continue
         match = expr.match( item)
         if not match: continue
         if match.group(0) != item: continue
         if FilesCount == 0: afile = item
         FilesCount += 1
         frame = int(item[prefixlen:-suffixlen])
         if framefirst == -1: framefirst = frame
         if framelast  == -1: framelast  = frame
         if framefirst > frame: framefirst = frame
         if framelast  < frame: framelast  = frame
      if FilesCount <= 1:
         self.cmdField.setText(('None or only one file founded matching pattern.\n\
         prefix, padding, suffix = "%(prefix)s" %(padding)d "%(suffix)s\n"' % vars()) + expr.pattern)
         return InputFile, InputPattern, FilesCount, Identify
      self.sbFrameFirst.setRange( framefirst, framelast)
      self.sbFrameFirst.setValue( framefirst)
      self.sbFrameLast.setRange(  framefirst, framelast)
      self.sbFrameLast.setValue(  framelast)
      if sys.platform.find('win') == 0: afile = afile.replace('/','\\')
      if self.cbIdentify.isChecked():
         afile = os.path.join( inputdir, afile)
         identify = 'convert -identify "%s"'
         if sys.platform.find('win') == 0: identify += ' nul'
         else: identify += ' /dev/null'
         Identify = subprocess.Popen( identify % afile, shell=True, bufsize=100000, stdout=subprocess.PIPE).stdout.read()
         if len(Identify) < len(afile):
            self.cmdField.setText('Invalid image.\n%s' % afile)
            return InputFile, InputPattern, FilesCount, Identify
         if not isinstance( Identify, str): Identify = str( Identify, 'utf-8')
         Identify = Identify.strip()
         Identify = Identify.replace( afile, '')
      InputPattern = os.path.join( inputdir, pattern)

      return InputFile, InputPattern, FilesCount, Identify

   def validateEditColor( self, string, message):
      if string is None: return False
      if string == '': return True
      values = string.split(',')
      if len( values) == 3:
         passed = True
         for value in values:
            if len( value) < 1 or len(value) > 3:
               passed = False
               break
            for digit in value:
               if not digit in '1234567890':
                  passed = False
                  break
         if passed: return True
      self.cmdField.setText('Invalid %s color string. Example: "255,255,0" - yellow.' % message)
      return False


   def evaluate( self):
      if not self.constructed: return
      self.evaluated = False
      self.btnStart.setEnabled( False)
      if self.running: return
      if self.decodeEvaluate(): return
      self.decode = False
      self.cmdField.clear()
      
      if not self.validateEditColor( str(self.editLine169.text()), 'line 16:9'): return
      if not self.validateEditColor( str(self.editLine235.text()), 'line 2.35'): return

      if self.inputPattern is None:
         self.cmdField.setText('Specify input sequence.')
         return

      audiofile = '%s' % self.audioInputFileName.text()
      if len(audiofile):
         audiofile = os.path.abspath( os.path.normpath( audiofile))
         if not os.path.isfile( audiofile):
            self.cmdField.setText('Error: Audio file does not exist.')
            return

      self.StereoDuplicate = self.cStereoDuplicate.isChecked()

      if self.cAutoTitles.isChecked(): self.editShot.clear()
      if self.cAutoOutputName.isChecked():
         self.editOutputName.clear()

      project = '%s' % self.editProject.text()
      if Options.project == '':
          if self.cAutoTitles.isChecked() or project == '':
            if sys.platform.find('win') == 0:
               pat_split = self.inputPattern.upper().split('\\')
               if len(pat_split) > 4: project = pat_split[4]
               else: project = pat_split[-1]
            else:
               pat_split = self.inputPattern.upper().split('/')
               if len(pat_split) > 3: project = pat_split[3]
               else: project = pat_split[-1]
            self.editProject.setText( project)

      shot = '%s' % self.editShot.text()
      if self.cAutoTitles.isChecked() or shot == '':
         shot = os.path.basename( self.inputPattern)[ : os.path.basename( self.inputPattern).find('.')]
         self.editShot.setText( shot)

      version = '%s' % self.editVersion.text()
      if self.cAutoTitles.isChecked() or version == '':
         version = os.path.basename( os.path.dirname(self.inputPattern))
         self.editVersion.setText( version)

      company  = '%s' % self.editCompany.text()
      artist   = '%s' % self.editArtist.text()
      activity = '%s' % self.editActivity.text()
      comments = '%s' % self.editComments.text()
      font     = '%s' % self.editFont.text()
      date     = time.strftime('%y%m%d')

      outdir = '%s' % self.editOutputDir.text()
      if outdir == '':
         outdir = os.path.dirname( os.path.dirname( self.inputPattern))
         self.editOutputDir.setText( outdir)

      outname = '%s' % self.editOutputName.text()
      if self.cAutoOutputName.isChecked() or outname == None or outname == '':
         outname = '%s' % self.editNaming.text()
         outname = outname.replace('(p)', project)
         outname = outname.replace('(P)', project.upper())
         outname = outname.replace('(s)', shot)
         outname = outname.replace('(S)', shot.upper())
         outname = outname.replace('(v)', version)
         outname = outname.replace('(V)', version.upper())
         outname = outname.replace('(d)', date)
         outname = outname.replace('(D)', date.upper())
         outname = outname.replace('(a)', activity)
         outname = outname.replace('(A)', activity.upper())
         outname = outname.replace('(c)', company)
         outname = outname.replace('(C)', company.upper())
         outname = outname.replace('(u)', artist)
         outname = outname.replace('(U)', artist.upper())
         self.editOutputName.setText( outname)

      lgspath = '%s' % self.editLgsPath.text()
      if lgspath != '':
         if not os.path.isfile( lgspath):
            if not os.path.isfile( os.path.join( LogosPath, lgspath)):
               self.cmdField.setText('No slate logo file founded')
               return

      lgfpath = '%s' % self.editLgfPath.text()
      if lgfpath != '':
         if not os.path.isfile( lgfpath):
            if not os.path.isfile( os.path.join( LogosPath, lgfpath)):
               self.cmdField.setText('No frame logo file founded')
               return

      cmd = 'makemovie.py'
      cmd = os.path.join( os.path.dirname( os.path.abspath( sys.argv[0])), cmd)
      cmd = '"%s" "%s"' % ( os.getenv('CGRU_PYTHONEXE','python'), cmd)
      cmd += ' -c "%s"' % getComboBoxString( self.cbCodec)
      cmd += ' -f %s' % self.cbFPS.currentText()
      cmd += ' -n %s' % self.cbContainer.currentText()
      cmd += ' --fs %d' % self.sbFrameFirst.value()
      cmd += ' --fe %d' % self.sbFrameLast.value()
      format = getComboBoxString( self.cbFormat)
      if format != '':
         if self.cFFFirst.isChecked(): cmd += ' --fff'
         ts = self.cbTemplateS.currentText()
         tf = self.cbTemplateF.currentText()
         cmd += ' -r %s' % format
         cmd += ' -g %.2f' % self.dsbCorrGamma.value()
         if ts != '': cmd += ' -s "%s"' % ts
         if tf != '': cmd += ' -t "%s"' % tf
         if project  != '': cmd += ' --project "%s"'  % project
         if shot     != '': cmd += ' --shot "%s"'     % shot
         if version  != '': cmd += ' --ver "%s"'      % version
         if company  != '': cmd += ' --company "%s"'  % company
         if artist   != '': cmd += ' --artist "%s"'   % artist
         if activity != '': cmd += ' --activity "%s"' % activity
         if comments != '': cmd += ' --comments "%s"' % comments
         if font     != '': cmd += ' --font "%s"'     % font
         cmd += ' --tmpformat %s' % self.cbTempFormat.currentText()
         if len( self.eTempFormatOptions.text()): cmd += ' --tmpquality "%s"' % self.eTempFormatOptions.text()
         if self.dsbAspectIn.value()   > 0: cmd += ' --aspect_in %f' % self.dsbAspectIn.value()
         if self.dsbAutoAspect.value() > 0: cmd += ' --aspect_auto %f' % self.dsbAutoAspect.value()
         if self.dsbAspectOut.value()  > 0: cmd += ' --aspect_out %f' % self.dsbAspectOut.value()
         if not self.cCorrAuto.isChecked():     cmd += ' --noautocorr'
         if len( self.eCorrAux.text()): cmd += ' --correction "%s"' % self.eCorrAux.text()
         if self.cTime.isChecked(): cmd += ' --addtime'
         cacher = getComboBoxString( self.cbCacherOpacity)
         if cacher != '0':
            cmd += ' --cacher_aspect %f' % self.dsbCacherAspect.value()
            cmd += ' --cacher_opacity %s' % cacher
         if len( self.editCacherLine.text()):
            cmd += ' --line_aspect "%s"' % self.dsbCacherLineAspect.value()
            cmd += ' --line_color "%s"' % self.editCacherLine.text()
         cacher = getComboBoxString( self.cbCacher169)
         if cacher != '0': cmd += ' --draw169 %s' % cacher
         cacher = getComboBoxString( self.cbCacher235)
         if cacher != '0': cmd += ' --draw235 %s' % cacher
         if len( self.editLine169.text()): cmd += ' --line169 "%s"' % self.editLine169.text()
         if len( self.editLine235.text()): cmd += ' --line235 "%s"' % self.editLine235.text()
         if lgspath != '':
            cmd += ' --lgspath "%s"' % lgspath
            cmd += ' --lgssize %d' % self.sbLgsSize.value()
            cmd += ' --lgsgrav %s' % self.cbLgsGravity.currentText()
         if lgfpath != '':
            cmd += ' --lgfpath "%s"' % lgfpath
            cmd += ' --lgfsize %d' % self.sbLgfSize.value()
            cmd += ' --lgfgrav %s' % self.cbLgfGravity.currentText()
      if self.cDateOutput.isChecked(): cmd += ' --datesuffix'
      if self.cTimeOutput.isChecked(): cmd += ' --timesuffix'
      if self.StereoDuplicate and self.inputPattern2 is None:
         cmd += ' --stereo'
      if audiofile != '':
         cmd += ' --audio "%s"' % audiofile
         cmd += ' --afreq %d' % (self.audioFreqSB.value() * 1000)
         cmd += ' --akbits %d' % self.audioBitRateSB.value()
         cmd += ' --acodec "%s"' % getComboBoxString( self.audioCodecCB)
      if self.cAfanasy.isChecked() and not self.cAfOneTask.isChecked():
         cmd += ' -A'
         if self.sbAfCapConvert.value() != -1: cmd += ' --afconvcap %d' % self.sbAfCapConvert.value()
         if self.sbAfCapEncode.value()  != -1: cmd += ' --afenccap %d' % self.sbAfCapEncode.value()
      if Options.debug: cmd += ' --debug'

      cmd += ' "%s"' % self.inputPattern
      if self.inputPattern2 is not None: cmd += ' "%s"' % self.inputPattern2
      cmd += ' "%s"' % os.path.join( outdir, outname)

      self.cmdField.setText( cmd)
      self.evaluated = True
      self.btnStart.setEnabled( True)

   def execute( self):
#      self.evaluate()
      if not self.evaluated: return
      command = "%s" % self.cmdField.toPlainText()
      if len(command) == 0: return

      afanasy = False
      if self.cAfanasy.isChecked():
         if self.cAfOneTask.isChecked() or self.decode: afanasy = True
      if afanasy:
         self.btnStart.setEnabled( False)
         try:
            af = __import__('af', globals(), locals(), [])
         except:
            error = str(sys.exc_info()[1])
            print( error)
            self.cmdField.setText('Unable to import Afanasy Python module:\n' + error)
            return
         if self.decode:
            jobname = '%s' % self.decodeOutputSequence.text()
            jobname = os.path.basename( jobname)
         else:
            jobname = '%s' % self.editOutputName.text()
         job = af.Job( jobname.encode('utf-8'))
         block = af.Block('Make Movie', 'movgen')
         if self.sbAfPriority.value()  != -1: job.setPriority(    self.sbAfPriority.value())
         if self.sbAfMaxHosts.value()  != -1: job.setMaxHosts(    self.sbAfMaxHosts.value())
         if self.sbAfCapacity.value()  != -1: block.setCapacity(  self.sbAfCapacity.value())
         hostsmask         = '%s' % self.editAfHostsMask.text()
         hostsmaskexclude  = '%s' % self.editAfHostsMaskExclude.text()
         dependmask        = '%s' % self.editAfDependMask.text()
         dependmaskglobal  = '%s' % self.editAfDependMaskGlobal.text()
         if hostsmask        != '': job.setHostsMask(        hostsmask.encode('utf-8')        )
         if hostsmaskexclude != '': job.setHostsMaskExclude( hostsmaskexclude.encode('utf-8') )
         if dependmask       != '': job.setDependMask(       dependmask.encode('utf-8')       )
         if dependmaskglobal != '': job.setDependMaskGlobal( dependmaskglobal.encode('utf-8') )
         datetime = self.editAfTime.dateTime()
         if datetime > QtCore.QDateTime.currentDateTime(): job.setWaitTime( datetime.toTime_t())
         if self.cAfPause.isChecked(): job.pause()
         job.setNeedOS('')
         job.blocks.append( block)
         task = af.Task(('%s' % self.editOutputName.text()).encode('utf-8'))
         task.setCommand( command.encode('utf-8'))

         block.tasks.append( task)
         if job.send():
            self.cmdField.setText('Afanasy job was successfully sent.')
            if self.decode and self.decodeEncode.isChecked():
               self.editInputFiles.setText( self.decodeOutputAbs.text())
         else:
            self.cmdField.setText('Unable to send job to Afanasy server.')
      else:
         self.btnStart.setEnabled( False)
         self.btnRefresh.setEnabled( False)
         self.btnStop.setEnabled( True)
         self.cmdField.clear()
         self.running = True
         self.process = QtCore.QProcess( self)
         self.process.setProcessChannelMode( QtCore.QProcess.MergedChannels)
         QtCore.QObject.connect( self.process, QtCore.SIGNAL('error( int)'), self.processerror)
         QtCore.QObject.connect( self.process, QtCore.SIGNAL('finished( int)'), self.processfinished)
         QtCore.QObject.connect( self.process, QtCore.SIGNAL('readyRead()'), self.processoutput)
         print('\n################################################\n')
         print(command)
         self.process.start( command)

   def processerror( self, error):
      self.cmdField.setText('Failed to start a process.')
      self.processfinished( -1)

   def processfinished( self, exitCode):
      print('Exit code = %d' % exitCode)
      self.btnStop.setEnabled( False)
      self.btnRefresh.setEnabled( True)
      self.running = False
      if exitCode != 0: return
      self.cmdField.setText('Finished.')
      if self.decode and self.decodeEncode.isChecked():
         self.decodeEnable.setChecked( False)
         self.editInputFiles.setText( self.decodeOutputAbs.text())
         self.inputFileChanged()

   def processoutput( self):
      output = self.process.readAll().data()
      if not isinstance( output, str): output = str( output, 'utf-8')
      output = output.strip()
      print('%s' % output)
      self.cmdField.insertPlainText( output + '\n')
      self.cmdField.moveCursor( QtGui.QTextCursor.End)

   def processStop( self):
      if self.process.pid() is None or self.process.pid() == 0:
         self.cmdField.setText('The process was not running.')
         self.processfinished( -1)
         return
      self.cmdField.setText('Stopping %d ...' % self.process.pid())
      self.process.terminate()
      if sys.platform.find('win') == 0:
         self.process.kill()

def getComboBoxString( comboBox):
   data = comboBox.itemData( comboBox.currentIndex())
   if data is None: return ''
   if isinstance( data, str): return data
   return comboBox.itemData( comboBox.currentIndex()).toString()

app = QtGui.QApplication( sys.argv)
app.setWindowIcon( QtGui.QIcon( cgruutils.getIconFileName( Options.wndicon)))
dialog = Dialog()
dialog.show()
app.exec_()

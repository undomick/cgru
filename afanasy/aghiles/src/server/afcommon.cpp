#include "afcommon.h"

#include <fcntl.h>
#include <sys/errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/unistd.h>
#include <sys/wait.h>

#include "../libafanasy/environment.h"

#include "core.h"

#define AFOUTPUT
#undef AFOUTPUT
#include "../include/macrooutput.h"

FileQueue         * AFCommon::FileWriteQueue    = NULL;
MsgQueue          * AFCommon::MsgDispatchQueue  = NULL;
DBUpdateTaskQueue * AFCommon::DBUpTaskQueue     = NULL;
DBActionQueue     * AFCommon::DBUpdateQueue     = NULL;
CleanUpQueue      * AFCommon::CleanUpJobQueue   = NULL;
LogQueue          * AFCommon::OutputLogQueue    = NULL;

AFCommon::AFCommon( Core * core)
{
   MsgDispatchQueue = new MsgQueue(          "Sending Messages");
   FileWriteQueue   = new FileQueue(         "Writing Files");
   CleanUpJobQueue  = new CleanUpQueue(      "Jobs Cleanup");
   OutputLogQueue   = new LogQueue(          "Log Output");
   DBUpTaskQueue    = new DBUpdateTaskQueue( "AFDB_update_task",   core->getMonitors());
   DBUpdateQueue    = new DBActionQueue(     "AFDB_update",        core->getMonitors());
}

AFCommon::~AFCommon()
{
   if( FileWriteQueue )   delete FileWriteQueue;
   if( MsgDispatchQueue ) delete MsgDispatchQueue;
   if( CleanUpJobQueue )  delete CleanUpJobQueue;
   if( OutputLogQueue )   delete OutputLogQueue;
   if( DBUpTaskQueue )    delete DBUpTaskQueue;
   if( DBUpdateQueue )    delete DBUpdateQueue;
}

/*
bool AFCommon::detach()
{
   pid_t pid = fork();
   if( pid  >  0 ) return true;
   if( pid == -1 )
   {
      AFERRPE("AFCommon::detach: fork:");
      return true;
   }
   return false;
}

void AFCommon::catchDetached()
{
   int status;
   pid_t pid;
   while(( pid=waitpid(-1,&status,WNOHANG)) > 0)
      printf("AFCommon::catchDetached: Child execution finish catched, pid=%d.\n", pid);
}
*/

void AFCommon::executeCmd( const std::string & cmd)
{
   std::cout << af::time2str() << ": Executing command:\n" << cmd.c_str() << std::endl;
   if( system( cmd.c_str()))
   {
      AFERRPE("AFCommon::executeCmd: system: ")
   }
}

void AFCommon::saveLog( const std::list<std::string> & log, const std::string & dirname, const std::string & filename, int rotate)
{
   int lines = log.size();
   if( lines < 1) return;
   std::string bytes;
   for( std::list<std::string>::const_iterator it = log.begin(); it != log.end(); it++)
   {
      bytes += *it;
      bytes += "\n";
   }

   std::string path = filename;
   af::pathFilterFileName( path);
   path = dirname + '/' + path;

   FileData * filedata = new FileData( bytes.data(), bytes.length(), path, rotate);
   FileWriteQueue->pushFile( filedata);
}

bool AFCommon::writeFile( const char * data, const int length, const std::string & filename)
{
   if( filename.size() == 0)
   {
      QueueLogError("AFCommon::writeFile: File name is empty.");
      return false;
   }
   int fd = open( filename.c_str(), O_WRONLY | O_CREAT, 0777);
   if( fd == -1 )
   {
      QueueLogErrno( std::string("AFCommon::writeFile: ") + filename);
      return false;
   }
   int bytes = 0;
   while( bytes < length )
   {
      int written = write( fd, data+bytes, length-bytes);
      if( written == -1 )
      {
         QueueLogErrno( std::string("AFCommon::writeFile: ") + filename);
         close( fd);
         return false;
      }
      bytes += written;
   }
   close( fd);
   chmod( filename.c_str(), 0777);
   AFINFA("AFCommon::writeFile - \"%s\"", filename.toUtf8().data())
   return true;
}
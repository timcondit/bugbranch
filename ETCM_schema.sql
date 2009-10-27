USE [ETCM]
GO
/****** Object:  Table [dbo].[Issue]    Script Date: 10/26/2009 09:07:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Issue](
	[PRN] [int] NOT NULL,
	[RequestType] [nvarchar](50) NOT NULL,
	[Title] [nvarchar](max) NOT NULL,
	[AssignedTo] [nvarchar](500) NOT NULL,
	[ReportedBy] [nvarchar](500) NOT NULL,
	[Status] [nvarchar](100) NOT NULL,
	[Priority] [int] NOT NULL,
	[Severity] [nvarchar](100) NOT NULL,
	[DateReported] [datetime] NOT NULL,
	[DateFixed] [datetime] NULL,
	[DateClosed] [datetime] NULL,
	[AssignedToProject] [nvarchar](100) NOT NULL,
	[ReportedInVersion] [nvarchar](100) NOT NULL,
	[CodeReviewed] [nchar](3) NOT NULL,
	[Product] [nvarchar](500) NOT NULL,
	[Component] [nvarchar](500) NOT NULL,
 CONSTRAINT [PK_Issue] PRIMARY KEY CLUSTERED 
(
	[PRN] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  UserDefinedFunction [dbo].[FirstOfMonth]    Script Date: 10/26/2009 09:07:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns the first day of the month before the specified date
-- =============================================
CREATE FUNCTION [dbo].[FirstOfMonth] 
(
	@dateAndTime DATETIME
)
RETURNS DATETIME
AS
BEGIN
	-- Declare the return variable
	DECLARE @Result DATETIME

	-- Subtract off a number of days to get the same time on the first of the month
	SELECT @Result = DATEADD(DAY, 1-DATEPART(DAY, @dateAndTime), @dateAndTime)
	
	-- Subtract off the time portion
	SELECT @Result = DATEADD(HOUR, -DATEPART(HOUR, @Result), @Result)
	SELECT @Result = DATEADD(MINUTE, -DATEPART(MINUTE, @Result), @Result)
	SELECT @Result = DATEADD(SECOND, -DATEPART(SECOND, @Result), @Result)
	SELECT @Result = DATEADD(MILLISECOND, -DATEPART(MILLISECOND, @Result), @Result)

	RETURN @Result

END
GO
/****** Object:  UserDefinedFunction [dbo].[FirstOfWeek]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns the first day of the week before the specified date
-- =============================================
CREATE FUNCTION [dbo].[FirstOfWeek] 
(
	@dateAndTime DATETIME
)
RETURNS DATETIME
AS
BEGIN
	-- Declare the return variable
	DECLARE @Result DATETIME

	-- Subtract off a number of days to get the same time on Sunday
	SELECT @Result = DATEADD(DAY, 1-DATEPART(WEEKDAY, @dateAndTime), @dateAndTime)
	
	-- Subtract off the time portion
	SELECT @Result = DATEADD(HOUR, -DATEPART(HOUR, @Result), @Result)
	SELECT @Result = DATEADD(MINUTE, -DATEPART(MINUTE, @Result), @Result)
	SELECT @Result = DATEADD(SECOND, -DATEPART(SECOND, @Result), @Result)
	SELECT @Result = DATEADD(MILLISECOND, -DATEPART(MILLISECOND, @Result), @Result)

	RETURN @Result

END
GO
/****** Object:  UserDefinedFunction [dbo].[FirstOfDay]    Script Date: 10/26/2009 09:07:32 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns midnight before the specified date
-- =============================================
CREATE FUNCTION [dbo].[FirstOfDay] 
(
	@dateAndTime DATETIME
)
RETURNS DATETIME
AS
BEGIN
	-- Declare the return variable
	DECLARE @Result DATETIME

	-- Subtract off the time portion
	SELECT @Result = @dateAndTime
	SELECT @Result = DATEADD(HOUR, -DATEPART(HOUR, @Result), @Result)
	SELECT @Result = DATEADD(MINUTE, -DATEPART(MINUTE, @Result), @Result)
	SELECT @Result = DATEADD(SECOND, -DATEPART(SECOND, @Result), @Result)
	SELECT @Result = DATEADD(MILLISECOND, -DATEPART(MILLISECOND, @Result), @Result)

	RETURN @Result

END
GO
/****** Object:  UserDefinedFunction [dbo].[GetProjectDays]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/25/2009
-- Description:	Returns the dates of the days the project was active,
-- from the first reported issue to the last closed issue
-- =============================================
CREATE FUNCTION [dbo].[GetProjectDays] 
(
	@Project varchar(255)
)
RETURNS 
@DayDates TABLE 
(
	DayDate DATETIME
)
AS
BEGIN

	--DECLARE @ProjectWeekDates TABLE (WeekDate DATETIME)
	
	DECLARE @DayDate DATETIME
	SELECT @DayDate = dbo.FirstOfDay(MIN(DateReported))
	FROM dbo.Issue
	WHERE AssignedToProject = @Project

	WHILE @DayDate < (SELECT MAX(DateClosed) FROM dbo.Issue WHERE AssignedToProject = @Project)
	BEGIN
		INSERT @DayDates VALUES (@DayDate)
		SELECT @DayDate = DATEADD(DAY, 1, @DayDate)
	END

	RETURN
		
END
GO
/****** Object:  UserDefinedFunction [dbo].[GetNumIssuesByProjectStatus]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/29/2009
-- Description:	Returns the number of issues 
-- in the specified project with the specified
-- status.
-- =============================================
CREATE FUNCTION [dbo].[GetNumIssuesByProjectStatus]
(
	@Project nvarchar(255),
	@Status nvarchar(100)
)
RETURNS INT
AS
BEGIN
	DECLARE @numLeftReported INT
	SELECT @numLeftReported = COUNT(*)
		FROM Issue
		WHERE AssignedToProject = @Project
		AND Status = @Status

	RETURN @numLeftReported
END
GO
/****** Object:  UserDefinedFunction [dbo].[GetNumLeftNotResolved]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns the number of issues left
-- in the reported state at the time specified
-- =============================================
CREATE FUNCTION [dbo].[GetNumLeftNotResolved]
(
	@Project varchar(255),
	@QueryDate datetime
)
RETURNS INT
AS
BEGIN
	DECLARE @numLeftReported INT
	SELECT @numLeftReported = COUNT(*)
		FROM Issue
		WHERE AssignedToProject = @Project
		AND (DateFixed IS NULL -- hasn't been fixed
			OR DateFixed > @QueryDate -- or was fixed after the given date
			OR ([Status] <> 'Resolved' AND [Status] <> 'Closed')) -- or it isn't still fixed

	RETURN @numLeftReported
END
GO
/****** Object:  UserDefinedFunction [dbo].[GetNumLeftNotClosed]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns the number of issues left
-- in the resolved state at the time specified
-- =============================================
CREATE FUNCTION [dbo].[GetNumLeftNotClosed]
(
	@Project varchar(255),
	@QueryDate datetime
)
RETURNS INT
AS
BEGIN
	DECLARE @numLeftReported INT
	SELECT @numLeftReported = COUNT(*)
		FROM Issue
		WHERE AssignedToProject = @Project
		AND (DateClosed IS NULL -- hasn't been closed
			OR DateClosed > @QueryDate -- or was closed after the given date
			OR Status <> 'Closed') -- or it isn't still closed

	RETURN @numLeftReported
END
GO
/****** Object:  View [dbo].[ActiveProjects]    Script Date: 10/26/2009 09:07:34 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[ActiveProjects]
AS
SELECT DISTINCT TOP (100) PERCENT AssignedToProject AS Project
FROM         dbo.Issue
WHERE     (Status = 'Assigned' OR
                      Status = 'Resolved') AND (AssignedToProject <> 'No Planned Project')
ORDER BY Project
GO
EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPane1', @value=N'[0E232FF0-B466-11cf-A24F-00AA00A3EFFF, 1.00]
Begin DesignProperties = 
   Begin PaneConfigurations = 
      Begin PaneConfiguration = 0
         NumPanes = 4
         Configuration = "(H (1[41] 4[20] 2[14] 3) )"
      End
      Begin PaneConfiguration = 1
         NumPanes = 3
         Configuration = "(H (1 [50] 4 [25] 3))"
      End
      Begin PaneConfiguration = 2
         NumPanes = 3
         Configuration = "(H (1 [50] 2 [25] 3))"
      End
      Begin PaneConfiguration = 3
         NumPanes = 3
         Configuration = "(H (4 [30] 2 [40] 3))"
      End
      Begin PaneConfiguration = 4
         NumPanes = 2
         Configuration = "(H (1 [56] 3))"
      End
      Begin PaneConfiguration = 5
         NumPanes = 2
         Configuration = "(H (2 [66] 3))"
      End
      Begin PaneConfiguration = 6
         NumPanes = 2
         Configuration = "(H (4 [50] 3))"
      End
      Begin PaneConfiguration = 7
         NumPanes = 1
         Configuration = "(V (3))"
      End
      Begin PaneConfiguration = 8
         NumPanes = 3
         Configuration = "(H (1[56] 4[18] 2) )"
      End
      Begin PaneConfiguration = 9
         NumPanes = 2
         Configuration = "(H (1 [75] 4))"
      End
      Begin PaneConfiguration = 10
         NumPanes = 2
         Configuration = "(H (1[66] 2) )"
      End
      Begin PaneConfiguration = 11
         NumPanes = 2
         Configuration = "(H (4 [60] 2))"
      End
      Begin PaneConfiguration = 12
         NumPanes = 1
         Configuration = "(H (1) )"
      End
      Begin PaneConfiguration = 13
         NumPanes = 1
         Configuration = "(V (4))"
      End
      Begin PaneConfiguration = 14
         NumPanes = 1
         Configuration = "(V (2))"
      End
      ActivePaneConfig = 0
   End
   Begin DiagramPane = 
      Begin Origin = 
         Top = 0
         Left = 0
      End
      Begin Tables = 
         Begin Table = "Issue"
            Begin Extent = 
               Top = 6
               Left = 38
               Bottom = 231
               Right = 209
            End
            DisplayFlags = 280
            TopColumn = 3
         End
      End
   End
   Begin SQLPane = 
   End
   Begin DataPane = 
      Begin ParameterDefaults = ""
      End
      Begin ColumnWidths = 9
         Width = 284
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
         Width = 1500
      End
   End
   Begin CriteriaPane = 
      Begin ColumnWidths = 11
         Column = 1440
         Alias = 900
         Table = 1170
         Output = 720
         Append = 1400
         NewValue = 1170
         SortType = 1350
         SortOrder = 1410
         GroupBy = 1350
         Filter = 1350
         Or = 1350
         Or = 1350
         Or = 1350
      End
   End
End
' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'ActiveProjects'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_DiagramPaneCount', @value=1 , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'VIEW',@level1name=N'ActiveProjects'
GO
/****** Object:  UserDefinedFunction [dbo].[GetProjectWeeks]    Script Date: 10/26/2009 09:07:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/23/2009
-- Description:	Returns the dates of the weeks the project was active,
-- from the first reported issue to the last closed issue
-- =============================================
CREATE FUNCTION [dbo].[GetProjectWeeks] 
(
	@Project varchar(255)
)
RETURNS 
@WeekDates TABLE 
(
	WeekDate DATETIME
)
AS
BEGIN

	--DECLARE @ProjectWeekDates TABLE (WeekDate DATETIME)
	
	DECLARE @WeekDate DATETIME
	SELECT @WeekDate = dbo.FirstOfWeek(MIN(DateReported))
	FROM dbo.Issue
	WHERE AssignedToProject = @Project

	WHILE @WeekDate < (SELECT MAX(DateClosed) FROM dbo.Issue WHERE AssignedToProject = @Project)
	BEGIN
		INSERT @WeekDates VALUES (@WeekDate)
		SELECT @WeekDate = DATEADD(DAY, 7, @WeekDate)
	END

	RETURN
		
END
GO
/****** Object:  UserDefinedFunction [dbo].[GetWeeks]    Script Date: 10/26/2009 09:07:34 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/25/2009
-- Description:	Returns midnight of every sunday
-- in the specified range
-- =============================================
CREATE FUNCTION [dbo].[GetWeeks] 
(
	@StartDate DATETIME,
	@EndDate DATETIME
)
RETURNS 
@WeekDates TABLE 
(
	WeekDate DATETIME
)
AS
BEGIN

	DECLARE @WeekDate DATETIME
	SET @WeekDate = dbo.FirstOfWeek(@StartDate)

	WHILE @WeekDate <= @EndDate
	BEGIN
		INSERT @WeekDates VALUES (@WeekDate)
		SELECT @WeekDate = DATEADD(DAY, 7, @WeekDate)
	END

	RETURN
		
END
GO
/****** Object:  UserDefinedFunction [dbo].[GetWeekdays]    Script Date: 10/26/2009 09:07:34 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Envision
-- Create date: 9/25/2009
-- Description:	Returns midnight of every weekday
-- in the specified range
-- =============================================
CREATE FUNCTION [dbo].[GetWeekdays] 
(
	@StartDate DATETIME,
	@EndDate DATETIME
)
RETURNS 
@DayDates TABLE 
(
	DayDate DATETIME
)
AS
BEGIN

	DECLARE @DayDate DATETIME
	SET @DayDate = dbo.FirstOfDay(@StartDate)

	WHILE @DayDate <= @EndDate
	BEGIN
		IF DATEPART(WEEKDAY, @DayDate) <> 1 AND DATEPART(WEEKDAY, @DayDate) <> 7
		BEGIN
			INSERT @DayDates VALUES (@DayDate)
		END
		SELECT @DayDate = DATEADD(DAY, 1, @DayDate)
	END

	RETURN
		
END
GO
